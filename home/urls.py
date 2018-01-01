from .views import community_cfp_view
from .views import community_read_only_view
from .views import community_landing_view
from .views import CommunityCreate, CommunityUpdate
from .views import community_status_change
from .views import ParticipationUpdate
from .views import NotParticipating
from .views import ProjectUpdate
from .views import project_read_only_view
from .views import project_status_change

from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/add/$', CommunityCreate.as_view(), name='community-add'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/participate/$', ParticipationUpdate.as_view(), name='community-participate'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/dont-participate/$', NotParticipating.as_view(), name='community-not-participating'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/edit/$', CommunityUpdate.as_view(), name='community-update'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/add/$', ProjectUpdate.as_view(), name='project-participate'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/status/$', community_status_change, name='community-status'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/edit/$', ProjectUpdate.as_view(), name='project-participate'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/status/$', project_status_change, name='project-status'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/$', project_read_only_view, name='project-read-only'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/$', community_read_only_view, name='community-read-only'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<slug>[^/]+)/$', community_landing_view, name='community-landing'),
    url(r'^communities/cfp/$', community_cfp_view, name='community-cfp'),
]
