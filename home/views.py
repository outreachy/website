from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from registration.backends.simple.views import RegistrationView

from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import NewCommunity
from .models import Participation
from .models import RoundPage
from .models import Project

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


@method_decorator(login_required, name='dispatch')
class ComradeUpdate(UpdateView):
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
    participating_communities_ids = set(
            current_round.participation_set.values_list('community_id', flat=True)
            )
    all_communities = Community.objects.all()
    approved_communities = []
    pending_communities = []
    rejected_communities = []
    not_participating_communities = []
    for c in all_communities:
        if c.id in participating_communities_ids:
            participation_info = get_object_or_404(Participation, community=c, participating_round=current_round)
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

    # Try to see if this community is participating in the current round
    # and get the Participation object if so.
    try:
        participation_info = Participation.objects.get(community=community, participating_round=current_round)
        approved_projects = participation_info.project_set.filter(list_project=True)
        pending_projects = participation_info.project_set.filter(list_project=None)
        rejected_projects = participation_info.project_set.filter(list_project=False)
        pending_mentored_projects = participation_info.project_set.filter(mentorapproval__approved=False).distinct()
    except Participation.DoesNotExist:
        participation_info = None
        approved_projects = None
        pending_projects = None
        rejected_projects = None
        pending_mentored_projects = None

    coordinator = None
    approved_coordinator_list = None
    pending_coordinator_list = None
    rejected_coordinator_list = None
    if request.user.is_authenticated:
        try:
            coordinator = CoordinatorApproval.objects.get(community=community, coordinator=request.user.comrade)
        except CoordinatorApproval.DoesNotExist:
            pass

    try:
        approved_coordinator_list = CoordinatorApproval.objects.get(community=community, approved=True)
        pending_coordinator_list = CoordinatorApproval.objects.get(community=community, approved=None)
        rejected_coordinator_list = CoordinatorApproval.objects.get(community=community, approved=None)
    except CoordinatorApproval.DoesNotExist:
        pass

    return render(request, 'home/community_read_only.html',
            {
            'current_round' : current_round,
            'community': community,
            'participation_info': participation_info,
            'approved_projects': approved_projects,
            'pending_projects': pending_projects,
            'rejected_projects': rejected_projects,
            'pending_mentored_projects': pending_mentored_projects,
            'coordinator': coordinator,
            'approved_coordinator_list': approved_coordinator_list,
            'pending_coordinator_list': pending_coordinator_list,
            'rejected_coordinator_list': pending_coordinator_list,
            },
            )

def community_landing_view(request, round_slug, slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    community = get_object_or_404(Community, slug=slug)

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(Participation, community=community, participating_round=this_round)
    projects = get_list_or_404(participation_info.project_set, list_project=True)
    approved_projects = [p for p in projects if p.accepting_new_applicants]
    closed_projects = [p for p in projects if not p.accepting_new_applicants]

    return render(request, 'home/community_landing.html',
            {
            'current_round' : this_round,
            'community': community,
            'participation_info': participation_info,
            'approved_projects': approved_projects,
            'closed_projects': closed_projects,
            },
            )

class CommunityCreate(LoginRequiredMixin, CreateView):
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

        # FIXME: handle admins who haven't become Comrades.
        coordinator_status = CoordinatorApproval(coordinator=self.request.user.comrade, community=community, approved=True)
        coordinator_status.save()

        # When a new community is created, immediately redirect the coordinator
        # to gather information about their participation in this round
        return HttpResponseRedirect(reverse('community-participate',
            kwargs={'slug': self.object.slug}))

class CommunityUpdate(LoginRequiredMixin, UpdateView):
    model = Community
    fields = ['name', 'description']

@require_POST
def community_status_change(request, community_slug):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(Participation, community=community, participating_round=current_round)

    if 'approve' in request.POST:
        participation_info.list_community = True
        participation_info.save()
    if 'reject' in request.POST:
        participation_info.list_community = False
        participation_info.save()

    return HttpResponseRedirect(reverse('community-read-only',
            kwargs={'slug': community.slug}))

# TODO - make sure people can't say they will fund 0 interns
class ParticipationUpdate(UpdateView):
    model = Participation
    fields = ['interns_funded', 'cfp_text']

    #def test_func(self):
    #    community = get_object_or_404(Community, slug=self.kwargs['slug'])
    #    participating_round = RoundPage.objects.latest('internstarts')

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    # By overriding the get_object method, we reuse the URL for
    # both creating and updating information about a
    # community participating in the current round.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['slug'])
        participating_round = RoundPage.objects.latest('internstarts')
        try:
            participation_info = Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
            participation_info.reason_for_not_participating = ""
            # If a community initially says they won't participate,
            # but then changes their mind, we need to set the
            # community approval status to pending.
            if participation_info.list_community is False:
                participation_info.list_community = None
            return participation_info
        except Participation.DoesNotExist:
            return Participation(
                    community=community,
                    participating_round=participating_round)

    def get_success_url(self):
        return reverse('community-read-only', kwargs={'slug': self.object.community.slug})

class NotParticipating(ParticipationUpdate):
    fields = ['reason_for_not_participating']

    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['slug'])
        participating_round = RoundPage.objects.latest('internstarts')
        try:
            # If a community said they were participating but
            # needs to withdraw from this round
            participation_info = Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
            participation_info.interns_funded = 0
            participation_info.cfp_text = "{name} is not participating in this Outreachy internship round and is not accepting mentor project proposals or volunteers at this time.".format(name=community.name),
            participation_info.list_community = False
            return participation_info
        except Participation.DoesNotExist:
            # If a community says they can't participate at the beginning of a round,
            # create a new Participation object and set some values
            return Participation(
                    community=community,
                    participating_round=participating_round,
                    interns_funded=0,
                    cfp_text="{name} is not participating in this Outreachy internship round and is not accepting mentor project proposals or volunteers at this time.".format(name=community.name),
                    list_community=False,
            )

# This view is for mentors and coordinators to review project information and approve it
def project_read_only_view(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)
    project = get_object_or_404(Project, slug=project_slug)
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
            'current_round': current_round,
            'community': community,
            'project' : project,
            'approved_mentors': approved_mentors,
            'unapproved_mentors': unapproved_mentors,
            'comrade': comrade,
            },
            )

@method_decorator(login_required, name='dispatch')
class ProjectUpdate(UpdateView):
    model = Project
    fields = ['short_title', 'longevity', 'community_size', 'approved_license', 'accepting_new_applicants']

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    # By overriding the get_object method, we reuse the URL for
    # both creating and updating information about a
    # community participating in the current round.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        participating_round = RoundPage.objects.latest('internstarts')
        participation = get_object_or_404(Participation,
                    community=community,
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
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        return reverse('project-read-only',
                kwargs={'project_slug': self.object.slug,
                    'community_slug': community.slug})

@require_POST
def project_status_change(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(Participation, community=community, participating_round=current_round)
    project = get_object_or_404(Project, slug=project_slug, project_round=participation_info)

    if 'approve' in request.POST:
        project.list_project = True
        project.save()
    if 'reject' in request.POST:
        project.list_project = False
        project.save()

    return HttpResponseRedirect(reverse('project-read-only',
            kwargs={'project_slug': project.slug,
                'community_slug': community.slug}))

# Only superusers and the coordinator for the community should be able to approve project mentors.
@require_POST
def project_mentor_update(request, community_slug, project_slug, mentor_id):
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(Participation, community=community, participating_round=current_round)
    project = get_object_or_404(Project, slug=project_slug, project_round=participation_info)
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

    return HttpResponseRedirect(reverse('project-read-only',
            kwargs={'project_slug': project.slug,
                'community_slug': community.slug}))

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

    return HttpResponseRedirect(reverse('community-read-only',
            kwargs={'slug': community.slug}))
