from .views import community_cfp_view
from .views import community_read_only_view
from .views import community_landing_view
from .views import CommunityCreate, CommunityUpdate
from .views import community_coordinator_update
from .views import community_status_change
from .views import dashboard
from .views import ComradeUpdate
from .views import MentorApprovalUpdate
from .views import ParticipationUpdate
from .views import NotParticipating
from .views import ProjectUpdate
from .views import project_mentor_update
from .views import project_read_only_view
from .views import project_status_change
from .views import RegisterUser
from .views import PendingRegisterUser
from .views import ActivationView
from .views import ActivationCompleteView

from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/add/$', CommunityCreate.as_view(), name='community-add'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/participate/$', ParticipationUpdate.as_view(), name='community-participate'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/dont-participate/$', NotParticipating.as_view(), name='community-not-participating'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/edit/$', CommunityUpdate.as_view(), name='community-update'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/add/$', ProjectUpdate.as_view(), name='project-participate'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/status/$', community_status_change, name='community-status'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/coordinator-update/(?P<coordinator_id>[^/]+)/$', community_coordinator_update, name='community-coordinator-update'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/mentor-status/(?P<mentor_id>[^/]+)/$', project_mentor_update, name='project-mentor-status'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/mentor-create/$', MentorApprovalUpdate.as_view(), name='project-mentor-create'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/edit/$', ProjectUpdate.as_view(), name='project-participate'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/status/$', project_status_change, name='project-status'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/$', project_read_only_view, name='project-read-only'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/$', community_read_only_view, name='community-read-only'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<slug>[^/]+)/$', community_landing_view, name='community-landing'),
    url(r'^communities/cfp/$', community_cfp_view, name='community-cfp'),
    url(r'^dashboard/$', dashboard, name='dashboard'),
    url(r'^account/$', ComradeUpdate.as_view(), name='account'),
    url(r'^register/$', RegisterUser.as_view(), name='register'),
    url(r'^register/sent/$', PendingRegisterUser.as_view(), name='registration_complete'),
    url(r'^register/activate/(?P<activation_key>[-.:\w]+)/$', ActivationView.as_view(), name='registration_activate'),
    url(r'^register/activate/$', ActivationCompleteView.as_view(), name='registration_activation_complete'),
]
