from . import views

from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/add/$', views.CommunityCreate.as_view(), name='community-add'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/edit/$', views.CommunityUpdate.as_view(), name='community-update'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/notify/$', views.CommunityNotificationUpdate.as_view(), name='notify-me'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/coordinator/preview/(?P<username>[^/]+)/$', views.CoordinatorApprovalPreview.as_view(), name='coordinatorapproval-preview'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/coordinator/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.CoordinatorApprovalAction.as_view(), name='coordinatorapproval-action'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/project/(?P<project_slug>[^/]+)/mentor/preview/(?P<username>[^/]+)/$', views.MentorApprovalPreview.as_view(), name='mentorapproval-preview'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/project/(?P<project_slug>[^/]+)/mentor/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.MentorApprovalAction.as_view(), name='mentorapproval-action'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/project/(?P<project_slug>[^/]+)/skills/$', views.ProjectSkillsEditPage.as_view(), name='project-skills-edit'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/project/(?P<project_slug>[^/]+)/channels/$', views.CommunicationChannelsEditPage.as_view(), name='communication-channels-edit'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/project/(?P<project_slug>[^/]+)/$', views.project_read_only_view, name='project-read-only'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<action>[^/]+)-project/(?:(?P<project_slug>[^/]+)/)?$', views.ProjectAction.as_view(), name='project-action'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/(?P<action>[^/]+)/$', views.ParticipationAction.as_view(), name='participation-action'),
    url(r'^communities/cfp/(?P<slug>[^/]+)/$', views.community_read_only_view, name='community-read-only'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<slug>[^/]+)/$', views.community_landing_view, name='community-landing'),
    url(r'^communities/cfp/$', views.community_cfp_view, name='community-cfp'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^account/$', views.ComradeUpdate.as_view(), name='account'),
    url(r'^register/$', views.RegisterUser.as_view(), name='register'),
    url(r'^register/sent/$', views.PendingRegisterUser.as_view(), name='registration_complete'),
    url(r'^register/activate/(?P<activation_key>[-.:\w]+)/$', views.ActivationView.as_view(), name='registration_activate'),
    url(r'^register/activate/$', views.ActivationCompleteView.as_view(), name='registration_activation_complete'),
]
