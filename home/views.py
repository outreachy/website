from collections import defaultdict
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from registration.backends.hmac import views as hmac_views

from . import email

from .mixins import ApprovalStatusAction
from .mixins import ComradeRequiredMixin
from .mixins import Preview

from .models import ApprovalStatus
from .models import CommunicationChannel
from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import NewCommunity
from .models import Notification
from .models import Sponsorship
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
def community_read_only_view(request, community_slug):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    coordinator = None
    notification = None
    if request.user.is_authenticated:
        try:
            # Although the current user is authenticated, don't assume
            # that they have a Comrade instance. Instead check that the
            # approval's coordinator is attached to a User that matches
            # this one.
            coordinator = community.coordinatorapproval_set.get(coordinator__account=request.user)
        except CoordinatorApproval.DoesNotExist:
            pass
        try:
            notification = Notification.objects.get(comrade=request.user.comrade, community=community)
        except Notification.DoesNotExist:
            pass

    approved_coordinator_list = community.coordinatorapproval_set.approved()

    context = {
            'current_round' : current_round,
            'community': community,
            'coordinator': coordinator,
            'notification': notification,
            'approved_coordinator_list': approved_coordinator_list,
            }

    # Try to see if this community is participating in the current round
    # and get the Participation object if so.
    try:
        participation_info = Participation.objects.get(community=community, participating_round=current_round)
        context['participation_info'] = participation_info
        context['approved_projects'] = participation_info.project_set.approved()
    except Participation.DoesNotExist:
        pass

    return render(request, 'home/community_read_only.html', context)

# A Comrade wants to sign up to be notified when a community coordinator
# says this community is participating in a new round
# FIXME we need to deal with deleting these once a community signs up.
class CommunityNotificationUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    fields = []

    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        try:
            return Notification.objects.get(comrade=self.request.user.comrade, community=community)
        except Notification.DoesNotExist:
            return Notification(comrade=self.request.user.comrade, community=community)

    def get_success_url(self):
        return self.object.community.get_preview_url()

def community_landing_view(request, round_slug, slug):
    # Try to see if this community is participating in that round
    # and if so, get the Participation object and related objects.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community', 'participating_round'),
            community__slug=slug,
            participating_round__slug=round_slug,
            )
    projects = get_list_or_404(participation_info.project_set.approved())
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

        # When a new community is created, immediately redirect the
        # coordinator to gather information about their participation in
        # this round. The Participation object doesn't have to be saved
        # to the database yet; that'll happen when they submit it in the
        # next step.
        return redirect(Participation(community=self.object).get_action_url('submit'))

class CommunityUpdate(LoginRequiredMixin, UpdateView):
    model = Community
    slug_url_kwarg = 'community_slug'
    fields = ['name', 'description', 'long_description', 'website']

    def get_object(self):
        community = super(CommunityUpdate, self).get_object()
        if not community.is_coordinator(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

    def get_success_url(self):
        return self.object.get_preview_url()

class SponsorshipInlineFormSet(BaseInlineFormSet):
    def get_queryset(self):
        qs = super(SponsorshipInlineFormSet, self).get_queryset()
        return qs.filter(coordinator_can_update=True)

    def save_new(self, form, commit=True):
        # Ensure that new objects created by this form will still be
        # editable with it later.
        form.instance.coordinator_can_update = True
        return super(SponsorshipInlineFormSet, self).save_new(form, commit)

class ParticipationAction(ApprovalStatusAction):
    form_class = inlineformset_factory(Participation, Sponsorship,
            formset=SponsorshipInlineFormSet,
            fields='__all__', exclude=['coordinator_can_update'])

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        participating_round = RoundPage.objects.latest('internstarts')
        try:
            return Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
        except Participation.DoesNotExist:
            return Participation(
                    community=community,
                    participating_round=participating_round)

    def get_context_data(self, **kwargs):
        context = super(ParticipationAction, self).get_context_data(**kwargs)
        context['readonly_sponsorships'] = self.object.sponsorship_set.filter(coordinator_can_update=False)
        return context

    def save_form(self, form):
        # We might be newly-creating the Participation or changing its
        # approval_status even though the form the user sees has no
        # fields off this object itself, so make sure to save it first
        # so it gets assigned a primary key.
        self.object.save()

        # InlineFormSet's save method returns the list of created or
        # changed Sponsorship objects, not the parent Participation.
        form.save()

        # Saving this form doesn't change which object is current.
        return self.object

    def notify(self):
        if self.prior_status == self.target_status:
            return

        if self.target_status == ApprovalStatus.PENDING:
            email.send_template_mail('home/email/community-signup.txt', {
                'community': self.object.community,
                'current_round': self.object.participating_round,
                'participation_info': self.object,
                },
                request=self.request,
                subject='Approve community participation - {name}'.format(name=self.object.community.name),
                recipient_list=[email.organizers])

            for notification in self.object.community.notification_set.all():
                email.send_template_mail('home/email/notify-mentors.txt', {
                    'community': self.object.community,
                    'notification': notification,
                    'current_round': self.object.participating_round,
                    },
                    request=self.request,
                    subject='Mentor for {name} in Outreachy'.format(name=self.object.community.name),
                    recipient_list=[notification.comrade.email_address()])
                notification.delete()

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

    approved_mentors = project.mentorapproval_set.approved()
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

class CoordinatorApprovalAction(ApprovalStatusAction):
    # We don't collect any information about coordinators beyond what's
    # in the Comrade model already.
    fields = []

    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])

        username = self.kwargs.get('username')
        if username:
            comrade = get_object_or_404(Comrade, account__username=username)
        else:
            comrade = self.request.user.comrade

        try:
            return CoordinatorApproval.objects.get(coordinator=comrade, community=community)
        except CoordinatorApproval.DoesNotExist:
            return CoordinatorApproval(coordinator=comrade, community=community)

class MentorApprovalAction(ApprovalStatusAction):
    fields = [
            'mentored_before',
            'mentorship_style',
            'longevity',
            'mentor_foss_contributions',
            'communication_channel_username',
            'instructions_read',
            'understands_intern_time_commitment',
            'understands_applicant_time_commitment',
            'understands_mentor_contract',
            ]

    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        project = get_object_or_404(Project,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=participating_round,
                slug=self.kwargs['project_slug'])

        username = self.kwargs.get('username')
        if username:
            mentor = get_object_or_404(Comrade, account__username=username)
        else:
            mentor = self.request.user.comrade

        try:
            approval = MentorApproval.objects.get(mentor=mentor, project=project)
        except MentorApproval.DoesNotExist:
            approval = MentorApproval(mentor=mentor, project=project)

        # Capture the old instructions_read before saving the form.
        self.instructions_already_read = approval.instructions_read
        return approval

    def get_success_url(self):
        if not self.instructions_already_read and self.object.project.is_submitter(self.request.user):
            # This is the first time this mentor has submitted this
            # form, but they're already approved, so we must be in the
            # middle of the "propose a new project" workflow.
            return reverse('project-skills-edit', kwargs={
                'community_slug': self.object.project.project_round.community.slug,
                'project_slug': self.object.project.slug,
                })

        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status == self.target_status:
            return

        if self.target_status == ApprovalStatus.PENDING:
            email.send_template_mail('home/email/mentor-review.txt', {
                'project': self.object.project,
                'community': self.object.project.project_round.community,
                'mentorapproval': self.object,
                },
                request=self.request,
                subject='Approve Outreachy mentor for {name}'.format(name=self.object.project.project_round.community.name),
                recipient_list=self.object.project.project_round.community.get_coordinator_email_list())
        elif self.target_status == ApprovalStatus.APPROVED:
            self.object.email_approved_mentor(self.request)

class ProjectAction(ApprovalStatusAction):
    fields = ['short_title', 'approved_license', 'unapproved_license_description', 'no_proprietary_software', 'proprietary_software_description', 'longevity', 'community_size', 'community_benefits', 'intern_tasks', 'intern_benefits', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'long_description', 'accepting_new_applicants']

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        participation = get_object_or_404(Participation,
                    community__slug=self.kwargs['community_slug'],
                    participating_round=participating_round)

        project_slug = self.kwargs.get('project_slug')
        if project_slug:
            return get_object_or_404(Project,
                    project_round=participation,
                    slug=project_slug)
        else:
            return Project(project_round=participation)

    def save_form(self, form):
        project = form.save(commit=False)

        if not project.slug:
            project.slug = slugify(project.short_title)[:project._meta.get_field('slug').max_length]

        project.save()
        return project

    def get_success_url(self):
        if not self.kwargs.get('project_slug'):
            # If this is a new Project, associate an approved mentor with it
            mentor = MentorApproval.objects.create(
                    mentor=self.request.user.comrade,
                    project=self.object,
                    approval_status=ApprovalStatus.APPROVED)
            return mentor.get_action_url('submit', self.request.user)
        elif self.kwargs['action'] == 'submit':
            return reverse('project-skills-edit', kwargs={
                'community_slug': self.object.project_round.community.slug,
                'project_slug': self.object.slug,
                })
        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status == self.target_status:
            return

        if self.target_status == ApprovalStatus.PENDING:
            # Only send email if this is a new project,
            # or someone withdrew a project and then resubmitted it.
            try:
                mentorapproval = self.object.mentorapproval_set.approved().get(
                        mentor=self.request.user.comrade)
            except MentorApproval.DoesNotExist:
                mentorapproval = None

            email.send_template_mail('home/email/project-review.txt', {
                'community': self.object.project_round.community,
                'project': self.object,
                'mentorapproval': mentorapproval,
                },
                request=self.request,
                subject='Approve Outreachy intern project proposal for {name}'.format(name=self.object.project_round.community.name),
                recipient_list=self.object.project_round.community.get_coordinator_email_list())

            if not self.object.approved_license or not self.object.no_proprietary_software:
                email.send_template_mail('home/email/project-warning.txt', {
                    'community': self.object.project_round.community,
                    'project': self.object,
                    'coordinator_list': self.object.project_round.community.get_coordinator_email_list(),
                    'mentor': mentorapproval.mentor,
                    },
                    request=self.request,
                    subject='Approve Outreachy intern project proposal for {name}'.format(name=self.object.project_round.community.name),
                    recipient_list=[email.organizers])

class BaseProjectEditPage(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=participating_round)
        if not project.is_submitter(self.request.user):
            raise PermissionDenied("You are not an approved mentor for this project.")
        return project

    def get_success_url(self):
        return reverse(self.next_view, kwargs=self.kwargs)

class ProjectSkillsEditPage(BaseProjectEditPage):
    template_name_suffix = '_skills_form'
    form_class = inlineformset_factory(Project, ProjectSkill, fields='__all__')
    next_view = 'communication-channels-edit'

class CommunicationChannelsEditPage(BaseProjectEditPage):
    template_name_suffix = '_channels_form'
    form_class = inlineformset_factory(Project, CommunicationChannel, fields='__all__')
    next_view = 'project-read-only'

class MentorApprovalPreview(Preview):
    def get_object(self):
        current_round = RoundPage.objects.latest('internstarts')
        return get_object_or_404(
                MentorApproval,
                project__slug=self.kwargs['project_slug'],
                project__project_round__participating_round=current_round,
                project__project_round__community__slug=self.kwargs['community_slug'],
                mentor__account__username=self.kwargs['username'])

class CoordinatorApprovalPreview(Preview):
    def get_object(self):
        return get_object_or_404(
                CoordinatorApproval,
                community__slug=self.kwargs['community_slug'],
                coordinator__account__username=self.kwargs['username'])

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

    by_status = defaultdict(list)
    for model in models:
        objects = model.objects_for_dashboard(request.user).distinct()
        for obj in objects:
            by_status[obj.approval_status].append((model._meta.verbose_name, obj))

    groups = []
    for status, label in ApprovalStatus.APPROVAL_STATUS_CHOICES:
        group = by_status.get(status)
        if group:
            groups.append((label, group))

    return render(request, 'home/dashboard.html', {
        'groups': groups,
        })
