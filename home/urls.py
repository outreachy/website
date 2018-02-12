from . import views

from django.conf.urls import include, url

# These views all take both a community_slug and a project_slug.
project_cfp_patterns = [
    url(r'^mentor/preview/(?P<username>[^/]+)/$', views.MentorApprovalPreview.as_view(), name='mentorapproval-preview'),
    url(r'^mentor/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.MentorApprovalAction.as_view(), name='mentorapproval-action'),
    url(r'^skills/$', views.ProjectSkillsEditPage.as_view(), name='project-skills-edit'),
    url(r'^channels/$', views.CommunicationChannelsEditPage.as_view(), name='communication-channels-edit'),
    url(r'^$', views.project_read_only_view, name='project-read-only'),
]

# These views all take a community_slug.
community_cfp_patterns = [
    url(r'^edit/$', views.CommunityUpdate.as_view(), name='community-update'),
    url(r'^notify/$', views.CommunityNotificationUpdate.as_view(), name='notify-me'),
    url(r'^coordinator/preview/(?P<username>[^/]+)/$', views.CoordinatorApprovalPreview.as_view(), name='coordinatorapproval-preview'),
    url(r'^coordinator/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.CoordinatorApprovalAction.as_view(), name='coordinatorapproval-action'),
    url(r'^project/(?P<project_slug>[^/]+)/', include(project_cfp_patterns)),
    url(r'^(?P<action>[^/]+)-project/(?:(?P<project_slug>[^/]+)/)?$', views.ProjectAction.as_view(), name='project-action'),
    url(r'^(?P<action>[^/]+)/$', views.ParticipationAction.as_view(), name='participation-action'),
    url(r'^$', views.community_read_only_view, name='community-read-only'),
]

urlpatterns = [
    url(r'^communities/cfp/add/$', views.CommunityCreate.as_view(), name='community-add'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/', include(community_cfp_patterns)),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/final-application/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.FinalApplicationAction.as_view(), name='application-action'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/contributions/add/$', views.ContributionUpdate.as_view(), name='contributions-add'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/contributions/(?P<contribution_slug>[^/]+)/$', views.ContributionUpdate.as_view(), name='contributions-edit'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/contributions/$', views.project_contributions, name='contributions'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/(?P<project_slug>[^/]+)/applicants/$', views.project_applicants, name='project-applicants'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<community_slug>[^/]+)/applicants/$', views.community_applicants, name='community-applicants'),
    url(r'^(?P<round_slug>[^/]+)/communities/(?P<slug>[^/]+)/$', views.community_landing_view, name='community-landing'),
    url(r'^communities/cfp/$', views.community_cfp_view, name='community-cfp'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^dashboard/trusted-volunteers/$', views.TrustedVolunteersListView.as_view(), name='trusted-volunteers-list'),
    url(r'^eligibility/$', views.EligibilityUpdateView.as_view(), name='eligibility'),
    url(r'^eligibility-results/$', views.eligibility_results, name='eligibility-results'),
    url(r'^account/$', views.ComradeUpdate.as_view(), name='account'),
    url(r'^apply/project-selection/$', views.current_round_page, name='project-selection'),
    url(r'^apply/make-contributions/$', views.contribution_tips, name='contribution-tips'),
    url(r'^apply/eligibility/$', views.eligibility_information, name='eligibility-information'),
    url(r'^register/$', views.RegisterUser.as_view(), name='register'),
    url(r'^register/sent/$', views.PendingRegisterUser.as_view(), name='registration_complete'),
    url(r'^register/activate/(?P<activation_key>[-.:\w]+)/$', views.ActivationView.as_view(), name='registration_activate'),
    url(r'^register/activate/$', views.ActivationCompleteView.as_view(), name='registration_activation_complete'),
]
