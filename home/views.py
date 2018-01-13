from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from registration.backends.hmac import views as hmac_views
from extra_views import UpdateWithInlinesView, InlineFormSet

from .models import ApprovalStatus
from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import NewCommunity
from .models import Participation
from .models import Project
from .models import ProjectSkill
from .models import RoundPage

class RegisterUser(hmac_views.RegistrationView):

    # The RegistrationView that django-registration provides
    # doesn't respect the next query parameter, so we have to
    # add it to the context of the template.
    def get_context_data(self, **kwargs):
        context = super(RegisterUser, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
        return context

    def get_activation_key(self, user):
        # The superclass implementation of get_activation_key will
        # serialize arbitrary data in JSON format, so we can save more
        # data than just the username, which is good! Unfortunately it
        # expects to get that data from the field named after whatever
        # string is in USERNAME_FIELD, which only works for actual
        # Django user models. So first we construct a fake user model
        # for it to take apart, containing only the data we want.
        self.USERNAME_FIELD = 'activation_data'
        self.activation_data = {'u': user.username}

        # Now, if we have someplace the user is supposed to go after
        # registering, then we save that as well.
        next_url = self.request.POST.get('next')
        if next_url:
            self.activation_data['n'] = next_url

        return super(RegisterUser, self).get_activation_key(self)

    def get_email_context(self, activation_key):
        return {
            'activation_key': activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'request': self.request,
        }

class PendingRegisterUser(TemplateView):
    template_name = 'registration/registration_complete.html'

class ActivationView(hmac_views.ActivationView):
    def get_user(self, data):
        # In the above RegistrationView, we dumped extra data into the
        # activation key, but the superclass implementation of get_user
        # expects the key to contain only a username string. So we save
        # our extra data and then pass the superclass the part it
        # expected.
        self.next_url = data.get('n')
        return super(ActivationView, self).get_user(data['u'])

    def get_success_url(self, user):
        # Ugh, we need to chain together TWO next-page URLs so we can
        # confirm that the person who posesses this activation token
        # also knows the corresponding password, then make a stop at the
        # ComradeUpdate form, before finally going where the user
        # actually wanted to go. Sorry folks.
        if self.next_url:
            query = '?' + urlencode({'next': self.next_url})
        else:
            query = ''
        query = '?' + urlencode({'next': reverse('account') + query})
        return reverse('registration_activation_complete') + query

class ActivationCompleteView(TemplateView):
    template_name = 'registration/activation_complete.html'

class ComradeUpdate(LoginRequiredMixin, UpdateView):
    model = Comrade

    # FIXME - we need a way for comrades to change their passwords
    # and update and re-verify their email address.
    fields = [
            'public_name',
            'nick_name',
            'legal_name',
            'pronouns',
            'pronouns_to_participants',
            'pronouns_public',
            'timezone',
            'primary_language',
            'second_language',
            'third_language',
            'fourth_language',
            ]

    # FIXME - we need to migrate any existing staff users who aren't a Comrade
    # to the Comrade model instead of the User model.
    def get_object(self):
        # Either grab the current comrade to update, or make a new one
        try:
            return self.request.user.comrade
        except Comrade.DoesNotExist:
            return Comrade(
                    account=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ComradeUpdate, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
        return context

    # FIXME - not sure where we should redirect people back to?
    # Take them back to the home page right now.
    def get_success_url(self):
        return self.request.POST.get('next', '/')

# Call for communities, mentors, and volunteers page
#
# This is complex, so class-based views don't help us here.
#
# We want to display four sections:
#  * Blurb about what Outreachy is
#  * Timeline for the round
#  * Communities that are participating and are open to mentors and volunteers
#  * Communities that have participated and need to be claimed by coordinators
#
# We need to end up with:
#  * The most current round (by round number)
#  * The communities participating in the current round (which have their CFP open)
#  * The communities which aren't participating in the current round
#
# We need to do some database calls in order to get this info:
#  * Grab all the rounds, sort by round number (descending), hand us back one round
#  * For the current round, grab all Participations (communities participating)
#  * Grab all the communities
#
# To get the communities which aren't participating:
#  * Make a set of the community IDs from the communities
#    participating in the current round (participating IDs)
#  * Walk through all communities, seeing if the community ID is
#    in participating IDs.
#    * If so, put it in a participating communities set
#    * If not, put it in a not participating communities set

def community_cfp_view(request):
    # FIXME: Grab data to display about communities and substitute into the template
    # Grab the most current round, based on the internship start date.
    # See https://docs.djangoproject.com/en/1.11/ref/models/querysets/#latest
    current_round = RoundPage.objects.latest('internstarts')

    # Now grab the community IDs of all communities participating in the current round
    # https://docs.djangoproject.com/en/1.11/topics/db/queries/#following-relationships-backward
    # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values-list
    # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values
    participating_communities = {
            p.community_id: p
            for p in current_round.participation_set.all()
            }
    all_communities = Community.objects.all().order_by('name')
    approved_communities = []
    pending_communities = []
    rejected_communities = []
    not_participating_communities = []
    for c in all_communities:
        participation_info = participating_communities.get(c.id)
        if participation_info is not None:
            if participation_info.approval_status == ApprovalStatus.PENDING:
                pending_communities.append(c)
            elif participation_info.approval_status == ApprovalStatus.APPROVED:
                approved_communities.append(c)
            else: # either withdrawn or rejected
                rejected_communities.append(c)
        else:
            not_participating_communities.append(c)

    # See https://docs.djangoproject.com/en/1.11/topics/http/shortcuts/
    return render(request, 'home/community_cfp.html',
            {
            'current_round' : current_round,
            'pending_communities': pending_communities,
            'approved_communities': approved_communities,
            'rejected_communities': rejected_communities,
            'not_participating_communities': not_participating_communities,
            },
            )

# This is the page for volunteers, mentors, and coordinators.
# It's a read-only page that displays information about the community,
# what projects are accepted, and how volunteers can help.
# If the community isn't participating in this round, the page displays
# instructions for being notified or signing the community up to participate.
def community_read_only_view(request, slug):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=slug)

    coordinator = None
    if request.user.is_authenticated:
        try:
            # Although the current user is authenticated, don't assume
            # that they have a Comrade instance. Instead check that the
            # approval's coordinator is attached to a User that matches
            # this one.
            coordinator = community.coordinatorapproval_set.get(coordinator__account=request.user)
        except CoordinatorApproval.DoesNotExist:
            pass

    newcommunity = None
    try:
        newcommunity = community.newcommunity
    except NewCommunity.DoesNotExist:
        pass

    approved_coordinator_list = community.coordinatorapproval_set.filter(approval_status=ApprovalStatus.APPROVED)
    pending_coordinator_list = community.coordinatorapproval_set.filter(approval_status=ApprovalStatus.PENDING)
    rejected_coordinator_list = community.coordinatorapproval_set.filter(approval_status__in=(ApprovalStatus.REJECTED, ApprovalStatus.WITHDRAWN))

    context = {
            'current_round' : current_round,
            'community': community,
            'newcommunity': newcommunity,
            'coordinator': coordinator,
            'approved_coordinator_list': approved_coordinator_list,
            'pending_coordinator_list': pending_coordinator_list,
            'rejected_coordinator_list': pending_coordinator_list,
            }
    template = 'home/community_not_participating_read_only.html'

    # Try to see if this community is participating in the current round
    # and get the Participation object if so.
    try:
        participation_info = Participation.objects.get(community=community, participating_round=current_round)
        context['participation_info'] = participation_info
        if participation_info.approval_status in (ApprovalStatus.PENDING, ApprovalStatus.APPROVED):
            context['approved_projects'] = participation_info.project_set.filter(approval_status=ApprovalStatus.APPROVED)
            context['pending_projects'] = participation_info.project_set.filter(approval_status=ApprovalStatus.PENDING)
            context['rejected_projects'] = participation_info.project_set.filter(approval_status__in=(ApprovalStatus.REJECTED, ApprovalStatus.WITHDRAWN))
            context['pending_mentored_projects'] = participation_info.project_set.filter(mentorapproval__approval_status=ApprovalStatus.PENDING).distinct()
        template = 'home/community_read_only.html'
    except Participation.DoesNotExist:
        pass

    return render(request, template, context)

def community_landing_view(request, round_slug, slug):
    # Try to see if this community is participating in that round
    # and if so, get the Participation object and related objects.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community', 'participating_round'),
            community__slug=slug,
            participating_round__slug=round_slug,
            )
    projects = get_list_or_404(participation_info.project_set, approval_status=ApprovalStatus.APPROVED)
    approved_projects = [p for p in projects if p.accepting_new_applicants]
    closed_projects = [p for p in projects if not p.accepting_new_applicants]

    return render(request, 'home/community_landing.html',
            {
            'participation_info': participation_info,
            'approved_projects': approved_projects,
            'closed_projects': closed_projects,
            # TODO: make the template get these off the participation_info instead of passing them in the context
            'current_round' : participation_info.participating_round,
            'community': participation_info.community,
            },
            )

# If the logged-in user doesn't have a Comrade object, redirect them to
# create one and then come back to the current page.
#
# Note that LoginRequiredMixin must be to the left of this class in the
# view's list of parent classes, and the base View must be to the right.
class ComradeRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            # Check that the logged-in user has a Comrade instance too:
            # even just trying to access the field will fail if not.
            request.user.comrade
        except Comrade.DoesNotExist:
            # If not, redirect to create one and remember to come back
            # here afterward.
            return redirect(
                    '{account_url}?{query_string}'.format(
                        account_url=reverse('account'),
                        query_string=urlencode({'next': request.path})))
        return super(ComradeRequiredMixin, self).dispatch(request, *args, **kwargs)

class CommunityCreate(LoginRequiredMixin, ComradeRequiredMixin, CreateView):
    model = NewCommunity
    fields = ['name', 'description', 'long_description', 'website',
            'community_size', 'longevity', 'participating_orgs',
            'approved_license', 'unapproved_license_description',
            'no_proprietary_software', 'proprietary_software_description',
            'goverance', 'code_of_conduct', 'cla', 'dco']

    # We have to over-ride this method because we need to
    # create a community's slug from its name.
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.slug = slugify(self.object.name)[:self.object._meta.get_field('slug').max_length]
        self.object.save()

        # Whoever created this community is automatically approved as a
        # coordinator for it, even though the community itself isn't
        # approved yet.
        CoordinatorApproval.objects.create(
                coordinator=self.request.user.comrade,
                community=self.object,
                approval_status=ApprovalStatus.APPROVED)

        # When a new community is created, immediately redirect the coordinator
        # to gather information about their participation in this round
        return redirect('community-participate', slug=self.object.slug)

class CommunityUpdate(LoginRequiredMixin, UpdateView):
    model = Community
    fields = ['name', 'description', 'long_description', 'website']

    def get_object(self):
        community = super(CommunityUpdate, self).get_object()
        if not community.is_coordinator(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

# Only Outreachy organizers are allowed to approve communities.
@require_POST
@login_required
def community_status_change(request, community_slug):
    current_round = RoundPage.objects.latest('internstarts')

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community'),
            community__slug=community_slug,
            participating_round=current_round)

    if not participation_info.is_approver(request.user):
        raise PermissionDenied("You are not an Outreachy organizer.")

    if 'approve' in request.POST:
        participation_info.approval_status = ApprovalStatus.APPROVED
        participation_info.save()
    if 'reject' in request.POST:
        participation_info.approval_status = ApprovalStatus.REJECTED
        participation_info.save()

    return redirect(participation_info.community.get_preview_url())

class ParticipationUpdateView(LoginRequiredMixin, UpdateView):
    model = Participation

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    # By overriding the get_object method, we reuse the URL for
    # both creating and updating information about a
    # community participating in the current round.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['slug'])
        participating_round = RoundPage.objects.latest('internstarts')
        try:
            participation = Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
        except Participation.DoesNotExist:
            participation = Participation(
                    approval_status=ApprovalStatus.WITHDRAWN,
                    community=community,
                    participating_round=participating_round)

        if not participation.is_submitter(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return participation

    def get_success_url(self):
        return self.object.community.get_preview_url()

# TODO - make sure people can't say they will fund 0 interns
class ParticipationUpdate(ParticipationUpdateView):
    fields = ['interns_funded', 'cfp_text']

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.reason_denied = ""

        if self.object.approval_status == ApprovalStatus.WITHDRAWN:
            # only send email when newly entering the pending state
            self.object.approval_status = ApprovalStatus.PENDING

            # render the email about this new community to a string
            email_string = render_to_string('home/email-community-signup.txt', {
                'community': self.object.community,
                'current_round': self.object.participating_round,
                'participation_info': self.object,
                }, request=self.request)
            send_mail(
                    from_email='Outreachy Organizers <organizers@outreachy.org>',
                    recipient_list=['organizers@outreachy.org'],
                    subject='Approve community participation - {name}'.format(name=self.object.community.name),
                    message=email_string)

        self.object.save()
        return redirect(self.get_success_url())


class NotParticipating(ParticipationUpdateView):
    fields = ['reason_denied']

    def get_object(self):
        participation_info = super(NotParticipating, self).get_object()
        participation_info.interns_funded = 0
        participation_info.approval_status = ApprovalStatus.WITHDRAWN
        return participation_info

# This view is for mentors and coordinators to review project information and approve it
def project_read_only_view(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    project = get_object_or_404(
            Project.objects.select_related('project_round__participating_round', 'project_round__community'),
            slug=project_slug,
            project_round__participating_round=current_round,
            project_round__community__slug=community_slug,
            )
    required_skills = project.projectskill_set.filter(required=ProjectSkill.STRONG)
    preferred_skills = project.projectskill_set.filter(required=ProjectSkill.OPTIONAL)
    bonus_skills = project.projectskill_set.filter(required=ProjectSkill.BONUS)

    approved_mentors = project.mentorapproval_set.filter(approval_status=ApprovalStatus.APPROVED)
    unapproved_mentors = project.mentorapproval_set.filter(approval_status__in=(ApprovalStatus.PENDING, ApprovalStatus.REJECTED))

    mentor_request = None
    coordinator = None
    if request.user.is_authenticated:
        try:
            # Although the current user is authenticated, don't assume
            # that they have a Comrade instance. Instead check that the
            # approval's mentor is attached to a User that matches
            # this one.
            mentor_request = project.mentorapproval_set.get(mentor__account=request.user)
        except MentorApproval.DoesNotExist:
            pass

        try:
            coordinator = project.project_round.community.coordinatorapproval_set.get(coordinator__account=request.user)
        except CoordinatorApproval.DoesNotExist:
            pass

    return render(request, 'home/project_read_only.html',
            {
            'current_round': project.project_round.participating_round,
            'community': project.project_round.community,
            'project' : project,
            'approved_mentors': approved_mentors,
            'unapproved_mentors': unapproved_mentors,
            'mentor_request': mentor_request,
            'coordinator': coordinator,
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'bonus_skills': bonus_skills,
            },
            )

class ProjectSkillsInline(InlineFormSet):
    model = ProjectSkill
    fields = '__all__'

class MentorApprovalUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    model = MentorApproval
    fields = [
            'mentored_before',
            'longevity',
            'communication_channel_username',
            'instructions_read',
            'understands_intern_time_commitment',
            'understands_applicant_time_commitment',
            'understands_mentor_contract',
            ]

    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        participation = get_object_or_404(Participation,
                    community__slug=self.kwargs['community_slug'],
                    participating_round=participating_round)
        project = get_object_or_404(Project,
                project_round=participation,
                slug=self.kwargs['project_slug'])

        try:
            return MentorApproval.objects.get(
                    mentor=self.request.user.comrade,
                    project=project)
        except MentorApproval.DoesNotExist:
            return MentorApproval(
                    mentor=self.request.user.comrade,
                    project=project,
                    approval_status=ApprovalStatus.WITHDRAWN)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.object.approval_status == ApprovalStatus.WITHDRAWN:
            self.object.approval_status = ApprovalStatus.PENDING
        self.object.save()
        return redirect(self.object.get_preview_url())

class ProjectUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateWithInlinesView):
    model = Project
    fields = ['short_title', 'approved_license', 'unapproved_license_description', 'no_proprietary_software', 'proprietary_software_description', 'longevity', 'community_size', 'intern_benefits', 'community_benefits', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'communication_tool', 'communication_url', 'communication_norms', 'communication_help', 'long_description', 'accepting_new_applicants']
    inlines = [ ProjectSkillsInline ]

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    # By overriding the get_object method, we reuse the URL for
    # both creating and updating information about a
    # community participating in the current round.
    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        participation = get_object_or_404(Participation,
                    community__slug=self.kwargs['community_slug'],
                    participating_round=participating_round)
        if 'project_slug' in self.kwargs:
            project = get_object_or_404(Project,
                    project_round=participation,
                    slug=self.kwargs['project_slug'])
        else:
            project = Project(project_round=participation)

        if not project.is_submitter(self.request.user):
            raise PermissionDenied("You are not an approved mentor for this project.")
        return project

    def forms_valid(self, form, inlines):
        self.object = form.save(commit=False)
        if not self.object.slug:
            self.object.slug = slugify(self.object.short_title)[:self.object._meta.get_field('slug').max_length]
        self.object.save()
        for formset in inlines:
            formset.save()
        if 'project_slug' not in self.kwargs:
            # If this is a new Project, associate an approved mentor with it
            MentorApproval.objects.create(
                    mentor=self.request.user.comrade,
                    project=self.object,
                    approval_status=ApprovalStatus.APPROVED)
            return redirect('project-mentor-create',
                community_slug=self.object.project_round.community.slug,
                project_slug=self.object.slug)
        return redirect(self.object.get_preview_url())

@require_POST
@login_required
def project_status_change(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    project = get_object_or_404(
            Project.objects.select_related('project_round__community'),
            slug=project_slug,
            project_round__participating_round=current_round,
            project_round__community__slug=community_slug,
            )

    if not project.is_approver(request.user):
        raise PermissionDenied("You are not an approved coordinator for this community.")

    if 'approve' in request.POST:
        project.approval_status = ApprovalStatus.APPROVED
        project.save()
    if 'reject' in request.POST:
        project.approval_status = ApprovalStatus.REJECTED
        project.save()

    return redirect(project.get_preview_url())

# Each of add/approve/reject requires different permissions, so read
# this carefully.
@require_POST
@login_required
def project_mentor_update(request, community_slug, project_slug, mentor_id):
    current_round = RoundPage.objects.latest('internstarts')

    # If this user doesn't have a Comrade object and wants to add
    # themself as a mentor, we'd like to help them by redirecting to the
    # ComradeUpdate form. (Approve and reject actions are guaranteed to
    # have a Comrade already so they're fine, at least.) But because
    # this is a POST request, we can't. This should be rare; just 404.
    mentor = get_object_or_404(Comrade, pk=mentor_id)

    mentor_status = get_object_or_404(
            MentorApproval,
            mentor=mentor,
            project__slug=project_slug,
            project__project_round__participating_round=current_round,
            project__project_round__community__slug=community_slug)

    if 'approve' in request.POST:
        if not mentor_status.is_approver(request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        mentor_status.approval_status = ApprovalStatus.APPROVED
        mentor_status.save()
    if 'reject' in request.POST:
        if not mentor_status.is_approver(request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        mentor_status.approval_status = ApprovalStatus.REJECTED
        mentor_status.save()
    if 'withdraw' in request.POST:
        if not mentor_status.is_submitter(request.user):
            raise PermissionDenied("You can only withdraw yourself, not other people.")
        mentor_status.approval_status = ApprovalStatus.WITHDRAWN
        mentor_status.save()

    return redirect(mentor_status.get_preview_url())

@require_POST
@login_required
def community_coordinator_update(request, community_slug, coordinator_id):
    community = get_object_or_404(Community, slug=community_slug)

    # See comment in project_mentor_update for why we just 404.
    coordinator = get_object_or_404(Comrade, account_id=coordinator_id)

    if 'add' in request.POST:
        coordinator_status = CoordinatorApproval(coordinator=coordinator, community=community, approval_status=ApprovalStatus.PENDING)
        if not coordinator_status.is_submitter(request.user):
            raise PermissionDenied("Hey, no fair volunteering other people without their consent!")
        coordinator_status.save()
    else:
        coordinator_status = get_object_or_404(CoordinatorApproval, coordinator=coordinator, community=community)

        if 'approve' in request.POST:
            if not coordinator_status.is_approver(request.user):
                raise PermissionDenied("You are not an approved coordinator for this community.")
            coordinator_status.approval_status = ApprovalStatus.APPROVED
            coordinator_status.save()
        if 'reject' in request.POST:
            if not coordinator_status.is_approver(request.user):
                raise PermissionDenied("You are not an approved coordinator for this community.")
            coordinator_status.approval_status = ApprovalStatus.REJECTED
            coordinator_status.save()
        if 'withdraw' in request.POST:
            if not coordinator_status.is_submitter(request.user):
                raise PermissionDenied("You can only withdraw yourself, not other people.")
            coordinator_status.approval_status = ApprovalStatus.WITHDRAWN
            coordinator_status.save()

    return redirect(community.get_preview_url())

@login_required
def dashboard(request):
    """
    Find objects for which the current user is either an approver or a
    submitter, and list them all on one page.
    """
    models = (
            CoordinatorApproval,
            Participation,
            Project,
            MentorApproval,
            )

    groups = [(label, group) for label, group in ((model._meta.verbose_name_plural, model.objects_for_dashboard(request.user)) for model in models) if group]

    return render(request, 'home/dashboard.html', {
        'groups': groups,
        })
