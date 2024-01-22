from . import dashboard, views
from .models import ApprovalStatus
from .models import InitialApplicationReview

from django.urls import include, re_path

# To see all URL patterns at once, run:
#   ./manage.py show_urls
# or to see just the patterns from this file:
#   ./manage.py show_urls | grep -Fw home.urls

# These views all take a community_slug.
community_cfp_patterns = [
    re_path(r'^edit/$', views.CommunityUpdate.as_view(), name='community-update'),
    re_path(r'^general-funding-application/(?P<new>[^/]+)/$', views.GeneralFundingApplication.as_view(), name='community-general-funding'),
    re_path(r'^notify/$', views.CommunityNotificationUpdate.as_view(), name='notify-me'),
    re_path(r'^coordinator/preview/(?P<username>[^/]+)/$', views.CoordinatorApprovalPreview.as_view(), name='coordinatorapproval-preview'),
    re_path(r'^coordinator/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.CoordinatorApprovalAction.as_view(), name='coordinatorapproval-action'),
    re_path(r'^$', views.community_read_only_view, name='community-read-only'),
]

# These views all take a round_slug, a community_slug, and a project_slug.
round_community_project_patterns = [
    re_path(r'^intern-agreement/$', views.InternAgreementSign.as_view(), name='intern-agreement'),
    re_path(r'^alum-standing/(?P<applicant_username>[^/]+)/(?P<standing>[^/]+)$', views.AlumStanding.as_view(), name='alum-standing'),
    re_path(r'^final-application/(?P<applicant_username>[^/]+)/select/$', views.InternSelectionUpdate.as_view(), name='select-intern'),
    re_path(r'^final-application/(?P<applicant_username>[^/]+)/remove/$', views.InternRemoval.as_view(), name='remove-intern'),
    re_path(r'^final-application/(?P<applicant_username>[^/]+)/resign/$', views.MentorResignation.as_view(), name='resign-as-mentor'),
    re_path(r'^final-application/(?P<applicant_username>[^/]+)/project-timeline/$', views.project_timeline, name='project-timeline'),
    re_path(r'^mentor-contract-export/(?P<applicant_username>[^/]+)/$', views.MentorContractExport.as_view(), name='mentor-contract'),
    re_path(r'^final-application/fund/(?P<applicant_username>[^/]+)/(?P<funding>[^/]+)$', views.InternFund.as_view(), name='intern-fund'),
    re_path(r'^final-application/organizer-approval/(?P<applicant_username>[^/]+)/(?P<approval>[^/]+)$', views.InternApprove.as_view(), name='intern-approval'),
    re_path(r'^final-application/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.FinalApplicationAction.as_view(), name='final-application-action'),
    re_path(r'^final-application/rate/(?P<username>[^/]+)/(?P<rating>[^/]+)$', views.FinalApplicationRate.as_view(), name='application-rate'),
    re_path(r'^contributions/add/$', views.ContributionUpdate.as_view(), name='contributions-add'),
    re_path(r'^contributions/(?P<contribution_id>\d+)/$', views.ContributionUpdate.as_view(), name='contributions-edit'),
    re_path(r'^contributions/$', views.ProjectContributions.as_view(), name='contributions'),
    re_path(r'^applicants/$', views.ProjectApplicants.as_view(), name='project-applicants'),
    re_path(r'^cfp/mentor/invite/$', views.InviteMentor.as_view(), name='mentorapproval-invite'),
    re_path(r'^cfp/mentor/preview/(?P<username>[^/]+)/$', views.MentorApprovalPreview.as_view(), name='mentorapproval-preview'),
    re_path(r'^cfp/mentor/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.MentorApprovalAction.as_view(), name='mentorapproval-action'),
    re_path(r'^cfp/skills/$', views.ProjectSkillsEditPage.as_view(), name='project-skills-edit'),
    re_path(r'^cfp/channels/$', views.CommunicationChannelsEditPage.as_view(), name='communication-channels-edit'),
    re_path(r'^cfp/$', views.project_read_only_view, name='project-read-only'),
]

# These views all take a round_slug and a community_slug.
round_community_patterns = [
    re_path(r'^(?P<project_slug>[^/]+)/', include(round_community_project_patterns)),
    re_path(r'^applicants/$', views.community_applicants, name='community-applicants'),
    re_path(r'^(?P<action>[^/]+)-project/(?:(?P<project_slug>[^/]+)/)?$', views.ProjectAction.as_view(), name='project-action'),
    re_path(r'^(?P<action>[^/]+)/$', views.ParticipationAction.as_view(), name='participation-action'),
    re_path(r'^$', views.community_landing_view, name='community-landing'),
]

# These views all take a round_slug.
round_patterns = [
    re_path(r'^communities/(?P<community_slug>[^/]+)/', include(round_community_patterns)),
    re_path(r'^contract-export/$', views.contract_export_view, name='contract-export'),
    re_path(r'^initial-feedback-export/$', views.initial_mentor_feedback_export_view, name='initial-feedback-export'),
    re_path(r'^initial-feedback-summary/$', views.initial_feedback_summary, name='initial-feedback-summary'),
    re_path(r'^midpoint-feedback-summary/$', views.midpoint_feedback_summary, name='midpoint-feedback-summary'),
    re_path(r'^feedback-3-export/$', views.feedback_3_export_view, name='feedback-3-export'),
    re_path(r'^feedback-3-summary/$', views.feedback_3_summary, name='feedback-3-summary'),
    re_path(r'^feedback-4-summary/$', views.feedback_4_summary, name='final-feedback-summary'),
    re_path(r'^sponsor-info/$', views.sponsor_info, name='sponsor-info'),
    re_path(r'^sponsor-info-details/(?P<community_slug>[^/]+)/', views.sponsor_info_details, name='sponsor-info-details'),
    re_path(r'^review-interns/$', views.ReviewInterns.as_view(), name='review-interns'),
] + [
    re_path(r'^email/{}/$'.format(event.slug), event.as_view(), name=event.url_name())
    for event in dashboard.all_round_events
]

urlpatterns = [
    re_path(r'^communities/cfp/add/$', views.CommunityCreate.as_view(), name='community-add'),
    re_path(r'^communities/cfp/participation-rules/$', views.CommunityParticipationRules.as_view(), name='community-participation-rules'),
    re_path(r'^communities/cfp/(?P<community_slug>[^/]+)/', include(community_cfp_patterns)),
    re_path(r'^communities/cfp/$', views.community_cfp_view, name='community-cfp'),
    re_path(r'^(?P<round_slug>[^/]+)/', include(round_patterns)),
    re_path(r'^intern-contract-export/$', views.intern_contract_export_view, name='intern-contract-export'),
    re_path(r'^generic-intern-contract-export/$', views.generic_intern_contract_export_view, name='generic-intern-contract-export'),
    re_path(r'^generic-mentor-contract-export/$', views.generic_mentor_contract_export_view, name='generic-mentor-contract-export'),
    re_path(r'^alums/$', views.alums_page, name='alums'),
    re_path(r'^alums/(?P<year>[1-9]\d*)-(?P<month>\d{2})/$', views.alums_page, name='cohort'),
    re_path(r'^dashboard/$', views.dashboard, name='dashboard'),
    re_path(r'^organizer-notes/(?P<comrade_pk>[^/]+)/$', views.OrganizerNotesUpdate.as_view(), name='organizer-notes'),
    # all pending applications
    re_path(r'^dashboard/pending-applications/$', views.applicant_review_summary, name='pending-applicants-summary', kwargs={'status': ApprovalStatus.PENDING, 'owner_username': 'all'}),
    re_path(r'^dashboard/unreviewed-unowned-pending-applications/$', views.applicant_review_summary, name='unreviewed-unowned-pending-applicants-summary', kwargs={'review_status': 'unreviewed', 'status': ApprovalStatus.PENDING}),
    re_path(r'^dashboard/unreviewed-unowned-non-student-pending-applications/$', views.applicant_review_summary, name='unreviewed-unowned-non-student-pending-applicants-summary', kwargs={'review_status': 'unreviewed-non-student', 'status': ApprovalStatus.PENDING}),
    re_path(r'^dashboard/pending-applications/(?P<owner_username>[^/]+)/$', views.applicant_review_summary, name='owned-pending-applicants-summary', kwargs={'status': ApprovalStatus.PENDING}),
    re_path(r'^dashboard/rejected-applications/$', views.applicant_review_summary, name='rejected-applicants-summary', kwargs={'status': ApprovalStatus.REJECTED, 'owner_username': 'all'}),
    re_path(r'^dashboard/approved-applications/$', views.applicant_review_summary, name='approved-applicants-summary', kwargs={'status': ApprovalStatus.APPROVED, 'owner_username': 'all'}),
    re_path(r'^dashboard/delete-application/(?P<applicant_username>[^/]+)/$', views.DeleteApplication.as_view(), name='delete-application'),
    re_path(r'^dashboard/process-applications/(?P<applicant_username>[^/]+)/$', views.ProcessInitialApplication.as_view(), name='process-application'),
    re_path(r'^dashboard/process-reviewed-applications/$', views.applicant_review_summary, name='process-reviewed-applications', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'process': True }),
    re_path(r'^dashboard/review-applications/(?P<applicant_username>[^/]+)/$', views.ViewInitialApplication.as_view(), name='applicant-review-detail'),
    re_path(r'^dashboard/review-applications/update-comment/(?P<applicant_username>[^/]+)/$', views.ReviewCommentUpdate.as_view(), name='update-comment'),
    re_path(r'^dashboard/review-applications/review-essay/(?P<applicant_username>[^/]+)/$', views.ReviewEssay.as_view(), name='review-essay'),
    re_path(r'^dashboard/review-applications/(?P<action>[^/]+)/(?P<applicant_username>[^/]+)/$', views.ApplicantApprovalUpdate.as_view(), name='initial-application-action'),
    re_path(r'^dashboard/review-applications/set-owner/(?P<owner>[^/]+)/(?P<applicant_username>[^/]+)/$', views.SetReviewOwner.as_view(), name='set-review-owner'),
    re_path(r'^dashboard/feedback/mentor/initial/(?P<username>[^/]+)/$', views.InitialMentorFeedbackUpdate.as_view(), name='initial-mentor-feedback'),
    re_path(r'^dashboard/feedback/intern/initial/$', views.InitialInternFeedbackUpdate.as_view(), name='initial-intern-feedback'),
    re_path(r'^dashboard/feedback/mentor/midpoint/(?P<username>[^/]+)/$', views.Feedback2FromMentorUpdate.as_view(), name='midpoint-mentor-feedback'),
    re_path(r'^dashboard/feedback/intern/midpoint/$', views.Feedback2FromInternUpdate.as_view(), name='midpoint-intern-feedback'),
    re_path(r'^dashboard/feedback/mentor/feedback-3/(?P<username>[^/]+)/$', views.Feedback3FromMentorUpdate.as_view(), name='feedback-3-from-mentor'),
    re_path(r'^dashboard/feedback/intern/feedback-3/$', views.Feedback3FromInternUpdate.as_view(), name='feedback-3-from-intern'),
    re_path(r'^dashboard/feedback/mentor/final/(?P<username>[^/]+)/$', views.Feedback4FromMentorUpdate.as_view(), name='final-mentor-feedback'),
    re_path(r'^dashboard/feedback/intern/final/$', views.Feedback4FromInternUpdate.as_view(), name='final-intern-feedback'),
    re_path(r'^dashboard/trusted-volunteers/$', views.TrustedVolunteersListView.as_view(), name='trusted-volunteers-list'),
    re_path(r'^dashboard/active-trusted-volunteers/$', views.ActiveTrustedVolunteersListView.as_view(), name='active-trusted-volunteers-list'),
    re_path(r'^dashboard/active-internship-contacts/$', views.ActiveInternshipContactsView.as_view(), name='active-internship-contacts'),
    re_path(r'^docs/$', views.docs_toc, name='docs'),
    re_path(r'^docs/applicant/$', views.docs_applicant, name='docs-applicant'),
    re_path(r'^docs/internship/$', views.docs_internship, name='docs-internship'),
    re_path(r'^docs/community/$', views.docs_community, name='docs-community'),
    re_path(r'^eligibility/$', views.EligibilityUpdateView.as_view(), name='eligibility'),
    re_path(r'^eligibility/essay-revision/(?P<applicant_username>[^/]+)/$', views.BarriersToParticipationUpdate.as_view(), name='essay-revision'),
    re_path(r'^eligibility/school-revision/(?P<applicant_username>[^/]+)/$', views.SchoolInformationUpdate.as_view(), name='school-revision'),
    re_path(r'^eligibility/request-essay-revision/(?P<applicant_username>[^/]+)/$', views.NotifyEssayNeedsUpdating.as_view(), name='request-essay-revision'),
    re_path(r'^eligibility/request-school-info-revision/(?P<applicant_username>[^/]+)/$', views.NotifySchoolInformationUpdating.as_view(), name='request-school-info-revision'),
    re_path(r'^eligibility-results/$', views.EligibilityResults.as_view(), name='eligibility-results'),
    re_path(r'^account/$', views.ComradeUpdate.as_view(), name='account'),
    re_path(r'^apply/project-selection/$', views.current_round_page, name='project-selection'),
    re_path(r'^past-projects/$', views.past_rounds_page, name='past-rounds'),
    re_path(r'^promote/$', views.promote_page, name='promote'),
    re_path(r'^apply/eligibility/$', views.eligibility_information, name='eligibility-information'),
    re_path(r'^register/$', views.RegisterUser.as_view(), name='register'),
    re_path(r'^register/sent/$', views.PendingRegisterUser.as_view(), name='django_registration_complete'),
    re_path(r'^register/activate/(?P<activation_key>[-.:\w]+)/$', views.ActivationView.as_view(), name='django_registration_activate'),
    re_path(r'^register/activate/$', views.ActivationCompleteView.as_view(), name='django_registration_activation_complete'),
    re_path(r'^rename-project-skills/$', views.ProjectSkillsRename.as_view(), name='rename-project-skills'),
    re_path(r'^internship-cohort-statistics/$', views.internship_cohort_statistics, name='internship-cohort-statistics'),
    re_path(r'^informal-chat-contacts/$', views.InformalChatContacts.as_view(), name='informal-chat-contacts'),
    re_path(r'^sponsor/donate/$', views.donate, name='donate'),
    re_path(r'^sponsor/$', views.sponsor, name='sponsor'),
    re_path(r'^edit-sponsorship/(?P<pk>[^/]+)/$', views.SponsorshipUpdate.as_view(), name='edit-sponsorship'),
    re_path(r'^opportunities/$', views.opportunities, name='opportunities'),
    re_path(r'^blog/(?P<round_slug>[^/]+)/application-period-statistics/$', views.round_statistics, name='blog-application-period-statistics'),
    re_path(r'^blog/2019-07-23/outreachy-schedule-changes/$', views.blog_schedule_changes, name='blog-schedule-changes'),
    re_path(r'^blog/2019-10-01/pick-a-project/$', views.blog_2019_pick_projects, name='2019-12-pick-a-project'),
    re_path(r'^blog/2019-10-18/open-projects/$', views.blog_2019_10_18_open_projects, name='2019-12-project-promotion'),
    re_path(r'^blog/2020-03-27/outreachy-response-to-covid-19/$', views.blog_2020_03_covid, name='2020-03-covid'),
    re_path(r'^blog/2020-08-28/december-2020-internship-applications-open/$', views.blog_2020_08_23_initial_applications_open, name='2020-08-initial-apps-open'),
    re_path(r'^blog/2021-01-15/may-2021-community-cfp-open/$', views.blog_2021_01_15_community_cfp_open, name='2021-01-community-cfp-open'),
    re_path(r'^blog/2021-02-01/may-2021-initial-applications-open/$', views.blog_2021_02_01_initial_applications_open, name='2021-01-initial-applications-open'),
    re_path(r'^blog/2021-03-23/fsf-participation-barred/$', views.blog_2021_03_23_fsf_participation_barred, name='2021-03-fsf-participation-barred'),
    re_path(r'^blog/2021-03-30/contribution-period-open/$', views.blog_2021_03_30_contribution_period_open, name='2021-03-contribution-period-open'),
    re_path(r'^blog/2021-08-13/december-2021-initial-applications-open/$', views.blog_2021_08_13_initial_applications_open, name='2021-08-initial-applications-open'),
    re_path(r'^blog/2021-08-18/december-2021-call-for-mentoring-communities/$', views.blog_2021_08_18_cfp_open, name='2021-08-cfp-open'),
    re_path(r'^blog/2021-10-14/hiring-for-an-outreachy-community-manager/$', views.blog_2021_10_outreachy_hiring, name='2021-10-outreachy-hiring'),
    re_path(r'^blog/2022-01-10/may-2022-call-for-mentoring-communities/$', views.blog_2022_01_10_cfp_open, name='2022-01-cfp-open'),
    re_path(r'^blog/2022-02-04/may-2022-initial-applications-open/$', views.blog_2022_02_04_initial_applications_open, name='2022-02-initial-applications-open'),
    re_path(r'^blog/2022-04-15/outreachy-welcomes-new-community-manager/$', views.blog_2022_04_15_new_community_manager, name='2022-04-new-community-manager'),
    re_path(r'^blog/2022-06-14/remembering-and-honoring-marina-zhurakhinskaya-founder-of-outreachy/$', views.blog_2022_06_14_remembering_marina, name='2022-06-remembering-marina'),
    re_path(r'^blog/2022-08-09/december-2022-initial-applications-open/$', views.blog_2022_08_09_initial_applications_open, name='2022-08-initial-applications-open'),
    re_path(r'^blog/2022-12-05/thank-you-december-2022-mentors-and-coordinators/$', views.blog_2022_12_05_thank_you, name='2022-12-thank-you'),
    re_path(r'^blog/2023-01-05/may-2023-call-for-mentoring-organizations/$', views.blog_2023_01_05_cfp_open, name='2023-01-cfp-open'),
    re_path(r'^blog/2023-01-16/may-2023-initial-applications-open/$', views.blog_2023_01_16_initial_applications_open, name='2023-01-initial-applications-open'),
    re_path(r'^blog/2023-08-01/december-2023-call-for-mentoring-organizations/$', views.blog_2023_08_01_cfp_open, name='2023-08-cfp-open'),
    re_path(r'^blog/2023-08-08/december-2023-initial-applications-open/$', views.blog_2023_08_08_initial_applications_open, name='2023-08-initial-applications-open'),
    re_path(r'^blog/2023-08-24/outreachy-welcomes-mentor-advocate/$', views.blog_2023_08_24_tilda, name='2023-08-tilda'),
    re_path(r'^blog/2024-01-08/may-2024-call-for-mentoring-organizations/$', views.blog_2024_01_08_cfp_open, name='2024-01-cfp-open'),
    re_path(r'^blog/2024-01-11/outreachy-2023-in-review/$', views.blog_outreachy_2023_year_in_review, name='outreachy-2023-year-in-review'),
    re_path(r'^blog/2024-01-15/may-2024-initial-applications-open/$', views.blog_2024_01_15_initial_applications_open, name='2024-01-initial-applications-open'),

    re_path(r'^privacy-policy/$', views.privacy_policy, name='privacy-policy'),
]
