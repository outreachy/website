from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from registration.backends.simple.views import RegistrationView

from .models import Community
from .models import Participation
from .models import RoundPage
from .models import Project

class CreateUser(RegistrationView):
    def get_success_url(self, user):
        return self.request.GET.get('next', '/')

    # The RegistrationView that django-registration provides
    # doesn't respect the next query parameter, so we have to
    # add it to the context of the template.
    def get_context_data(self, **kwargs):
        context = super(CreateUser, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next')
        return context

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
    participating_communities = []
    not_participating_communities = []
    for c in all_communities:
        if c.id in participating_communities_ids:
            participating_communities.append(c)
        else:
            not_participating_communities.append(c)

    # See https://docs.djangoproject.com/en/1.11/topics/http/shortcuts/
    return render(request, 'home/community_cfp.html',
            {
            'current_round' : current_round,
            'participating_communities': participating_communities,
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
        approved_projects = get_list_or_404(participation_info.project_set, list_project=True)
        pending_projects = get_list_or_404(participation_info.project_set, list_project=False)
    except Participation.DoesNotExist:
        participation_info = None
        approved_projects = None
        pending_projects = None

    return render(request, 'home/community_read_only.html',
            {
            'current_round' : current_round,
            'community': community,
            'participation_info': participation_info,
            'approved_projects': approved_projects,
            'pending_projects': pending_projects,
            },
            )

def community_landing_view(request, round_slug, slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    community = get_object_or_404(Community, slug=slug)

    # Try to see if this community is participating in that round
    # and get the Participation object if so.
    participation_info = get_object_or_404(Participation, community=community, participating_round=this_round)
    projects = get_list_or_404(participation_info.project_set, list_project=True)

    return render(request, 'home/community_landing.html',
            {
            'current_round' : this_round,
            'community': community,
            'participation_info': participation_info,
            'approved_projects': projects,
            },
            )

class CommunityCreate(CreateView):
    model = Community
    fields = ['name', 'description']
    
    # We have to over-ride this method because we need to
    # create a community's slug from its name.
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.slug = slugify(self.object.name)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

class CommunityUpdate(UpdateView):
    model = Community
    fields = ['name', 'description']
