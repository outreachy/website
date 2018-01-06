from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, UpdateView

from registration.backends.simple.views import RegistrationView

from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import NewCommunity
from .models import Participation
from .models import Project
from .models import RoundPage

class RegisterUser(RegistrationView):

    # The RegistrationView that django-registration provides
    # doesn't respect the next query parameter, so we have to
    # add it to the context of the template.
    def get_context_data(self, **kwargs):
        context = super(RegisterUser, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
        return context

    def get_success_url(self, user):
        return '{account_url}?{query_string}'.format(
                account_url=reverse('account'),
                query_string=urlencode({'next': self.request.POST.get('next', '/')}))


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
    all_communities = Community.objects.all()
    approved_communities = []
    pending_communities = []
    rejected_communities = []
    not_participating_communities = []
    for c in all_communities:
        participation_info = participating_communities.get(c.id)
        if participation_info is not None:
            if participation_info.list_community is None:
                pending_communities.append(c)
            elif participation_info.list_community is True:
                approved_communities.append(c)
            else:
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

    approved_coordinator_list = community.coordinatorapproval_set.filter(approved=True)
    pending_coordinator_list = community.coordinatorapproval_set.filter(approved=None)
    rejected_coordinator_list = community.coordinatorapproval_set.filter(approved=False)

    context = {
            'current_round' : current_round,
            'community': community,
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
        context['approved_projects'] = participation_info.project_set.filter(list_project=True)
        context['pending_projects'] = participation_info.project_set.filter(list_project=None)
        context['rejected_projects'] = participation_info.project_set.filter(list_project=False)
        context['pending_mentored_projects'] = participation_info.project_set.filter(mentorapproval__approved=False).distinct()
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
    projects = get_list_or_404(participation_info.project_set, list_project=True)
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
    fields = ['name', 'description', 'community_size', 'longevity', 'participating_orgs',
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
                approved=True)

        # When a new community is created, immediately redirect the coordinator
        # to gather information about their participation in this round
        return redirect('community-participate', slug=self.object.slug)

class CommunityUpdate(LoginRequiredMixin, UpdateView):
    model = Community
    fields = ['name', 'description']

    def get_object(self):
        community = super(CommunityUpdate, self).get_object()
        if not community.coordinatorapproval_set.filter(approved=True, coordinator__account=self.request.user).exists():
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

@require_POST
@staff_member_required
def community_status_change(request, community_slug):
    current_round = RoundPage.objects.latest('internstarts')

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community'),
            community__slug=community_slug,
            participating_round=current_round)

    if 'approve' in request.POST:
        participation_info.list_community = True
        participation_info.save()
    if 'reject' in request.POST:
        participation_info.list_community = False
        participation_info.save()

    return redirect(participation_info.community)

class ParticipationUpdateView(LoginRequiredMixin, UpdateView):
    model = Participation

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    # By overriding the get_object method, we reuse the URL for
    # both creating and updating information about a
    # community participating in the current round.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['slug'])
        if not community.coordinatorapproval_set.filter(approved=True, coordinator__account=self.request.user).exists():
            raise PermissionDenied("You are not an approved coordinator for this community.")

        participating_round = RoundPage.objects.latest('internstarts')
        try:
            return Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
        except Participation.DoesNotExist:
            return Participation(
                    community=community,
                    participating_round=participating_round)

    def get_success_url(self):
        return self.object.community.get_absolute_url()

# TODO - make sure people can't say they will fund 0 interns
class ParticipationUpdate(ParticipationUpdateView):
    fields = ['interns_funded', 'cfp_text']

    def get_object(self):
        participation_info = super(ParticipationUpdate, self).get_object()
        # If a community initially says they won't participate,
        # but then changes their mind, we need to set the
        # community approval status to pending.
        participation_info.reason_for_not_participating = ""
        if participation_info.list_community is False:
            participation_info.list_community = None
        return participation_info

class NotParticipating(ParticipationUpdateView):
    fields = ['reason_for_not_participating']

    def get_object(self):
        participation_info = super(NotParticipating, self).get_object()
        participation_info.interns_funded = 0
        participation_info.list_community = False
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
    approved_mentors = [x.mentor for x in MentorApproval.objects.filter(project=project)
            if x.approved is True]
    unapproved_mentors = [x.mentor for x in MentorApproval.objects.filter(project=project)
            if x.approved is False]
    if request.user:
        # FIXME: force Comrade creation
        comrade = get_object_or_404(Comrade, account=request.user)
    else:
        comrade = None

    return render(request, 'home/project_read_only.html',
            {
            'current_round': project.project_round.participating_round,
            'community': project.project_round.community,
            'project' : project,
            'approved_mentors': approved_mentors,
            'unapproved_mentors': unapproved_mentors,
            'comrade': comrade,
            },
            )

class ProjectUpdate(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['short_title', 'longevity', 'community_size', 'approved_license', 'accepting_new_applicants']

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
            return get_object_or_404(Project,
                    project_round=participation,
                    slug=self.kwargs['project_slug'])
        else:
            return Project(project_round=participation)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not self.object.slug:
            self.object.slug = slugify(self.object.short_title)[:self.object._meta.get_field('slug').max_length]
        self.object.save()
        if 'project_slug' not in self.kwargs:
            # If this is a new Project, associate an approved mentor with it
            MentorApproval.objects.create(
                    mentor=self.request.user.comrade,
                    project=self.object, approved=True)
        return redirect('project-read-only',
                project_slug=self.object.slug,
                community_slug=self.object.project_round.community.slug)

@require_POST
def project_status_change(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    project = get_object_or_404(
            Project,
            slug=project_slug,
            project_round__participating_round=current_round,
            project_round__community__slug=community_slug,
            )

    if 'approve' in request.POST:
        project.list_project = True
        project.save()
    if 'reject' in request.POST:
        project.list_project = False
        project.save()

    return redirect('project-read-only',
            project_slug=project_slug,
            community_slug=community_slug)

# Only superusers and the coordinator for the community should be able to approve project mentors.
@require_POST
def project_mentor_update(request, community_slug, project_slug, mentor_id):
    current_round = RoundPage.objects.latest('internstarts')
    project = get_object_or_404(
            Project,
            slug=project_slug,
            project_round__participating_round=current_round,
            project_round__community__slug=community_slug,
            )

    # FIXME: redirect to a Comrade creation view with next pointing back to this
    mentor = get_object_or_404(Comrade, account_id=mentor_id)

    if 'add' in request.POST:
        mentor_status = MentorApproval(mentor=mentor, project=project, approved=False)
        mentor_status.save()
    if 'approve' in request.POST:
        mentor_status = get_object_or_404(MentorApproval, mentor=mentor, project=project)
        mentor_status.approved = True
        mentor_status.save()
    if 'reject' in request.POST:
        mentor_status = get_object_or_404(MentorApproval, mentor=mentor, project=project)
        # Yeah, this could be a NullBooleanField and we could tell mentors
        # that they have been rejected, but TBH I'm running out of time to fix this.
        mentor_status.delete()

    return redirect('project-read-only',
            project_slug=project_slug,
            community_slug=community_slug)

@require_POST
@login_required
def community_coordinator_update(request, community_slug, coordinator_id):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    # FIXME: redirect to a Comrade creation view with next pointing back to this
    coordinator = get_object_or_404(Comrade, account_id=coordinator_id)

    if 'add' in request.POST:
        coordinator_status = CoordinatorApproval(coordinator=coordinator, community=community, approved=None)
        coordinator_status.save()
    if 'approve' in request.POST:
        coordinator_status = get_object_or_404(CoordinatorApproval, coordinator=coordinator, community=community)
        coordinator_status.approved = True
        coordinator_status.save()
    if 'reject' in request.POST:
        coordinator_status = get_object_or_404(CoordinatorApproval, coordinator=coordinator, community=community)
        coordinator_status.approved = False
        coordinator_status.save()
    if 'withdraw' in request.POST:
        coordinator_status = get_object_or_404(CoordinatorApproval, coordinator=coordinator, community=community)
        coordinator_status.delete()

    return redirect(community)
