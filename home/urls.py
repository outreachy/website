from . import dashboard, views
from .models import ApprovalStatus
from .models import InitialApplicationReview

from django.views.generic import TemplateView
from django.conf.urls import include, url

# To see all URL patterns at once, run:
#   ./manage.py show_urls
# or to see just the patterns from this file:
#   ./manage.py show_urls | grep -Fw home.urls

# These views all take a community_slug.
community_cfp_patterns = [
    url(r'^edit/$', views.CommunityUpdate.as_view(), name='community-update'),
    url(r'^general-funding-application/(?P<new>[^/]+)/$', views.GeneralFundingApplication.as_view(), name='community-general-funding'),
    url(r'^notify/$', views.CommunityNotificationUpdate.as_view(), name='notify-me'),
    url(r'^coordinator/preview/(?P<username>[^/]+)/$', views.CoordinatorApprovalPreview.as_view(), name='coordinatorapproval-preview'),
    url(r'^coordinator/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.CoordinatorApprovalAction.as_view(), name='coordinatorapproval-action'),
    url(r'^$', views.community_read_only_view, name='community-read-only'),
]

# These views all take a round_slug, a community_slug, and a project_slug.
round_community_project_patterns = [
    url(r'^intern-agreement/$', views.InternAgreementSign.as_view(), name='intern-agreement'),
    url(r'^alum-standing/(?P<applicant_username>[^/]+)/(?P<standing>[^/]+)$', views.AlumStanding.as_view(), name='alum-standing'),
    url(r'^final-application/(?P<applicant_username>[^/]+)/select/$', views.InternSelectionUpdate.as_view(), name='select-intern'),
    url(r'^final-application/(?P<applicant_username>[^/]+)/remove/$', views.InternRemoval.as_view(), name='remove-intern'),
    url(r'^final-application/(?P<applicant_username>[^/]+)/resign/$', views.MentorResignation.as_view(), name='resign-as-mentor'),
    url(r'^final-application/(?P<applicant_username>[^/]+)/project-timeline/$', views.project_timeline, name='project-timeline'),
    url(r'^mentor-contract-export/(?P<applicant_username>[^/]+)/$', views.MentorContractExport.as_view(), name='mentor-contract'),
    url(r'^final-application/fund/(?P<applicant_username>[^/]+)/(?P<funding>[^/]+)$', views.InternFund.as_view(), name='intern-fund'),
    url(r'^final-application/organizer-approval/(?P<applicant_username>[^/]+)/(?P<approval>[^/]+)$', views.InternApprove.as_view(), name='intern-approval'),
    url(r'^final-application/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.FinalApplicationAction.as_view(), name='final-application-action'),
    url(r'^final-application/rate/(?P<username>[^/]+)/(?P<rating>[^/]+)$', views.FinalApplicationRate.as_view(), name='application-rate'),
    url(r'^contributions/add/$', views.ContributionUpdate.as_view(), name='contributions-add'),
    url(r'^contributions/(?P<contribution_id>\d+)/$', views.ContributionUpdate.as_view(), name='contributions-edit'),
    url(r'^contributions/$', views.ProjectContributions.as_view(), name='contributions'),
    url(r'^applicants/$', views.ProjectApplicants.as_view(), name='project-applicants'),
    url(r'^cfp/mentor/invite/$', views.InviteMentor.as_view(), name='mentorapproval-invite'),
    url(r'^cfp/mentor/preview/(?P<username>[^/]+)/$', views.MentorApprovalPreview.as_view(), name='mentorapproval-preview'),
    url(r'^cfp/mentor/(?P<action>[^/]+)/(?:(?P<username>[^/]+)/)?$', views.MentorApprovalAction.as_view(), name='mentorapproval-action'),
    url(r'^cfp/skills/$', views.ProjectSkillsEditPage.as_view(), name='project-skills-edit'),
    url(r'^cfp/channels/$', views.CommunicationChannelsEditPage.as_view(), name='communication-channels-edit'),
    url(r'^cfp/$', views.project_read_only_view, name='project-read-only'),
]

# These views all take a round_slug and a community_slug.
round_community_patterns = [
    url(r'^(?P<project_slug>[^/]+)/', include(round_community_project_patterns)),
    url(r'^applicants/$', views.community_applicants, name='community-applicants'),
    url(r'^(?P<action>[^/]+)-project/(?:(?P<project_slug>[^/]+)/)?$', views.ProjectAction.as_view(), name='project-action'),
    url(r'^(?P<action>[^/]+)/$', views.ParticipationAction.as_view(), name='participation-action'),
    url(r'^$', views.community_landing_view, name='community-landing'),
]

# These views all take a round_slug.
round_patterns = [
    url(r'^communities/(?P<community_slug>[^/]+)/', include(round_community_patterns)),
    url(r'^contract-export/$', views.contract_export_view, name='contract-export'),
    url(r'^initial-feedback-export/$', views.initial_mentor_feedback_export_view, name='initial-feedback-export'),
    url(r'^initial-feedback-summary/$', views.initial_feedback_summary, name='initial-feedback-summary'),
    url(r'^midpoint-feedback-summary/$', views.midpoint_feedback_summary, name='midpoint-feedback-summary'),
    url(r'^feedback-3-export/$', views.feedback_3_export_view, name='feedback-3-export'),
    url(r'^feedback-3-summary/$', views.feedback_3_summary, name='feedback-3-summary'),
    url(r'^feedback-4-summary/$', views.feedback_4_summary, name='final-feedback-summary'),
    url(r'^sponsor-info/$', views.sponsor_info, name='sponsor-info'),
    url(r'^sponsor-info-details/(?P<community_slug>[^/]+)/', views.sponsor_info_details, name='sponsor-info-details'),
    url(r'^review-interns/$', views.ReviewInterns.as_view(), name='review-interns'),
] + [
    url(r'^email/{}/$'.format(event.slug), event.as_view(), name=event.url_name())
    for event in dashboard.all_round_events
]

urlpatterns = [
    url(r'^communities/cfp/add/$', views.CommunityCreate.as_view(), name='community-add'),
    url(r'^communities/cfp/participation-rules/$', views.community_participation_rules, name='community-participation-rules'),
    url(r'^communities/cfp/(?P<community_slug>[^/]+)/', include(community_cfp_patterns)),
    url(r'^communities/cfp/$', views.community_cfp_view, name='community-cfp'),
    url(r'^(?P<round_slug>[^/]+)/', include(round_patterns)),
    url(r'^intern-contract-export/$', views.intern_contract_export_view, name='intern-contract-export'),
    url(r'^generic-intern-contract-export/$', views.generic_intern_contract_export_view, name='generic-intern-contract-export'),
    url(r'^generic-mentor-contract-export/$', views.generic_mentor_contract_export_view, name='generic-mentor-contract-export'),
    url(r'^alums/$', views.alums_page, name='alums'),
    url(r'^alums/(?P<year>[1-9]\d*)-(?P<month>\d{2})/$', views.alums_page, name='cohort'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    # all pending applications
    url(r'^dashboard/pending-applications/$', views.applicant_review_summary, name='pending-applicants-summary', kwargs={'status': ApprovalStatus.PENDING, 'owner_username': 'all'}),
    url(r'^dashboard/strong-reviewed-applications/$', views.applicant_review_summary, name='strong-reviewed-applicants', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.STRONG }),
    url(r'^dashboard/good-reviewed-applications/$', views.applicant_review_summary, name='good-reviewed-applicants', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.GOOD }),
    url(r'^dashboard/maybe-reviewed-applications/$', views.applicant_review_summary, name='maybe-reviewed-applicants', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.MAYBE }),
    url(r'^dashboard/unclear-reviewed-applications/$', views.applicant_review_summary, name='unclear-reviewed-applicants', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.UNCLEAR }),
    url(r'^dashboard/unreviewed-unowned-pending-applications/$', views.applicant_review_summary, name='unreviewed-unowned-pending-applicants-summary', kwargs={'review_status': 'unreviewed', 'status': ApprovalStatus.PENDING}),
    url(r'^dashboard/unreviewed-unowned-non-student-pending-applications/$', views.applicant_review_summary, name='unreviewed-unowned-non-student-pending-applicants-summary', kwargs={'review_status': 'unreviewed-non-student', 'status': ApprovalStatus.PENDING}),
    url(r'^dashboard/reviewed-unowned-pending-applications/$', views.applicant_review_summary, name='reviewed-unowned-pending-applicants-summary', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING}),
    url(r'^dashboard/pending-applications/(?P<owner_username>[^/]+)/$', views.applicant_review_summary, name='owned-pending-applicants-summary', kwargs={'status': ApprovalStatus.PENDING}),
    url(r'^dashboard/rejected-applications/$', views.applicant_review_summary, name='rejected-applicants-summary', kwargs={'status': ApprovalStatus.REJECTED, 'owner_username': 'all'}),
    url(r'^dashboard/approved-applications/$', views.applicant_review_summary, name='approved-applicants-summary', kwargs={'status': ApprovalStatus.APPROVED, 'owner_username': 'all'}),
    url(r'^dashboard/delete-application/(?P<applicant_username>[^/]+)/$', views.DeleteApplication.as_view(), name='delete-application'),
    url(r'^dashboard/process-applications/(?P<applicant_username>[^/]+)/$', views.ProcessInitialApplication.as_view(), name='process-application'),
    url(r'^dashboard/process-strong-applications/$', views.applicant_review_summary, name='process-strong-applications', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.STRONG, 'process': True }),
    url(r'^dashboard/process-good-applications/$', views.applicant_review_summary, name='process-good-applications', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.GOOD, 'process': True }),
    url(r'^dashboard/process-maybe-applications/$', views.applicant_review_summary, name='process-maybe-applications', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.MAYBE, 'process': True }),
    url(r'^dashboard/process-unclear-applications/$', views.applicant_review_summary, name='process-unclear-applications', kwargs={'review_status': 'reviewed', 'status': ApprovalStatus.PENDING, 'rating': InitialApplicationReview.UNCLEAR, 'process': True }),
    url(r'^dashboard/review-applications/(?P<applicant_username>[^/]+)/$', views.ViewInitialApplication.as_view(), name='applicant-review-detail'),
    url(r'^dashboard/review-applications/update-comment/(?P<applicant_username>[^/]+)/$', views.ReviewCommentUpdate.as_view(), name='update-comment'),
    url(r'^dashboard/review-applications/review-essay/(?P<applicant_username>[^/]+)/$', views.ReviewEssay.as_view(), name='review-essay'),
    url(r'^dashboard/review-applications/(?P<action>[^/]+)/(?P<applicant_username>[^/]+)/$', views.ApplicantApprovalUpdate.as_view(), name='initial-application-action'),
    url(r'^dashboard/review-applications/rate-essay/(?P<rating>[^/]+)/(?P<applicant_username>[^/]+)/$', views.EssayRating.as_view(), name='essay-rating'),
    url(r'^dashboard/review-applications/change-red-flag/(?P<flag>[^/]+)/(?P<flag_value>[^/]+)/(?P<applicant_username>[^/]+)/$', views.ChangeRedFlag.as_view(), name='change-red-flag'),
    url(r'^dashboard/review-applications/set-owner/(?P<owner>[^/]+)/(?P<applicant_username>[^/]+)/$', views.SetReviewOwner.as_view(), name='set-review-owner'),
    url(r'^dashboard/feedback/mentor/initial/(?P<username>[^/]+)/$', views.InitialMentorFeedbackUpdate.as_view(), name='initial-mentor-feedback'),
    url(r'^dashboard/feedback/intern/initial/$', views.InitialInternFeedbackUpdate.as_view(), name='initial-intern-feedback'),
    url(r'^dashboard/feedback/mentor/midpoint/(?P<username>[^/]+)/$', views.Feedback2FromMentorUpdate.as_view(), name='midpoint-mentor-feedback'),
    url(r'^dashboard/feedback/intern/midpoint/$', views.Feedback2FromInternUpdate.as_view(), name='midpoint-intern-feedback'),
    url(r'^dashboard/feedback/mentor/feedback-3/(?P<username>[^/]+)/$', views.Feedback3FromMentorUpdate.as_view(), name='feedback-3-from-mentor'),
    url(r'^dashboard/feedback/intern/feedback-3/$', views.Feedback3FromInternUpdate.as_view(), name='feedback-3-from-intern'),
    url(r'^dashboard/feedback/mentor/final/(?P<username>[^/]+)/$', views.Feedback4FromMentorUpdate.as_view(), name='final-mentor-feedback'),
    url(r'^dashboard/feedback/intern/final/$', views.Feedback4FromInternUpdate.as_view(), name='final-intern-feedback'),
    url(r'^dashboard/trusted-volunteers/$', views.TrustedVolunteersListView.as_view(), name='trusted-volunteers-list'),
    url(r'^dashboard/active-trusted-volunteers/$', views.ActiveTrustedVolunteersListView.as_view(), name='active-trusted-volunteers-list'),
    url(r'^dashboard/active-internship-contacts/$', views.ActiveInternshipContactsView.as_view(), name='active-internship-contacts'),
    url(r'^docs/$', views.docs_toc, name='docs'),
    url(r'^docs/applicant/$', views.docs_applicant, name='docs-applicant'),
    url(r'^docs/internship/$', views.docs_internship, name='docs-internship'),
    url(r'^docs/community/$', views.docs_community, name='docs-community'),
    url(r'^eligibility/$', views.EligibilityUpdateView.as_view(), name='eligibility'),
    url(r'^eligibility/essay-revision/(?P<applicant_username>[^/]+)/$', views.BarriersToParticipationUpdate.as_view(), name='essay-revision'),
    url(r'^eligibility/school-revision/(?P<applicant_username>[^/]+)/$', views.SchoolInformationUpdate.as_view(), name='school-revision'),
    url(r'^eligibility/request-essay-revision/(?P<applicant_username>[^/]+)/$', views.NotifyEssayNeedsUpdating.as_view(), name='request-essay-revision'),
    url(r'^eligibility/request-school-info-revision/(?P<applicant_username>[^/]+)/$', views.NotifySchoolInformationUpdating.as_view(), name='request-school-info-revision'),
    url(r'^eligibility-results/$', views.EligibilityResults.as_view(), name='eligibility-results'),
    url(r'^longitudinal-survey/2018-initiate/$', views.Survey2018Notification.as_view(), name='longitudinal-survey-2018-initiate'),
    url(r'^longitudinal-survey/2018/(?P<survey_slug>[^/]+)/$', views.AlumSurveyUpdate.as_view(), name='longitudinal-survey-2018'),
    url(r'^longitudinal-survey/2018-completed/$', TemplateView.as_view(template_name='home/survey_confirmation.html'), name='longitudinal-survey-2018-completed'),
    url(r'^longitudinal-survey/2018-opt-out/(?P<survey_slug>[^/]+)/$', views.survey_opt_out, name='longitudinal-survey-2018-opt-out'),
    url(r'^account/$', views.ComradeUpdate.as_view(), name='account'),
    url(r'^apply/project-selection/$', views.current_round_page, name='project-selection'),
    url(r'^past-projects/$', views.past_rounds_page, name='past-rounds'),
    url(r'^promote/$', views.promote_page, name='promote'),
    url(r'^apply/eligibility/$', views.eligibility_information, name='eligibility-information'),
    url(r'^register/$', views.RegisterUser.as_view(), name='register'),
    url(r'^register/sent/$', views.PendingRegisterUser.as_view(), name='django_registration_complete'),
    url(r'^register/activate/(?P<activation_key>[-.:\w]+)/$', views.ActivationView.as_view(), name='django_registration_activate'),
    url(r'^register/activate/$', views.ActivationCompleteView.as_view(), name='django_registration_activation_complete'),
    url(r'^rename-project-skills/$', views.ProjectSkillsRename.as_view(), name='rename-project-skills'),
    url(r'^internship-cohort-statistics/$', views.internship_cohort_statistics, name='internship-cohort-statistics'),
    url(r'^informal-chat-contacts/$', views.InformalChatContacts.as_view(), name='informal-chat-contacts'),
    url(r'^sponsor/donate/$', views.donate, name='donate'),
    url(r'^sponsor/$', views.sponsor, name='sponsor'),
    url(r'^opportunities/$', views.opportunities, name='opportunities'),
    url(r'^blog/(?P<round_slug>[^/]+)/application-period-statistics/$', views.round_statistics, name='blog-application-period-statistics'),
    url(r'^blog/2019-07-23/outreachy-schedule-changes/$', views.blog_schedule_changes, name='blog-schedule-changes'),
    url(r'^blog/2019-10-01/pick-a-project/$', views.blog_2019_pick_projects, name='2019-12-pick-a-project'),
    url(r'^blog/2019-10-18/open-projects/$', views.blog_2019_10_18_open_projects, name='2019-12-project-promotion'),
    url(r'^blog/2020-03-27/outreachy-response-to-covid-19/$', views.blog_2020_03_covid, name='2020-03-covid'),
    url(r'^blog/2020-08-28/december-2020-internship-applications-open/$', views.blog_2020_08_23_initial_applications_open, name='2020-08-initial-apps-open'),
    url(r'^blog/2021-01-15/may-2021-community-cfp-open/$', views.blog_2021_01_15_community_cfp_open, name='2021-01-community-cfp-open'),
    url(r'^blog/2021-02-01/may-2021-initial-applications-open/$', views.blog_2021_02_01_initial_applications_open, name='2021-01-initial-applications-open'),
    url(r'^blog/2021-03-23/fsf-participation-barred/$', views.blog_2021_03_23_fsf_participation_barred, name='2021-03-fsf-participation-barred'),
    url(r'^blog/2021-03-30/contribution-period-open/$', views.blog_2021_03_30_contribution_period_open, name='2021-03-contribution-period-open'),
    url(r'^blog/2021-08-13/december-2021-initial-applications-open/$', views.blog_2021_08_13_initial_applications_open, name='2021-08-initial-applications-open'),
    url(r'^blog/2021-08-18/december-2021-call-for-mentoring-communities/$', views.blog_2021_08_18_cfp_open, name='2021-08-cfp-open'),
    url(r'^blog/2021-10-14/hiring-for-an-outreachy-community-manager/$', views.blog_2021_10_outreachy_hiring, name='2021-10-outreachy-hiring'),
    url(r'^blog/2022-01-10/may-2022-call-for-mentoring-communities/$', views.blog_2022_01_10_cfp_open, name='2022-01-cfp-open'),
    url(r'^blog/2022-02-04/may-2022-initial-applications-open/$', views.blog_2022_02_04_initial_applications_open, name='2022-02-initial-applications-open'),
    url(r'^blog/2022-04-15/outreachy-welcomes-new-community-manager/$', views.blog_2022_04_15_new_community_manager, name='2022-04-new-community-manager'),
    url(r'^blog/2022-06-14/remembering-and-honoring-marina-zhurakhinskaya-founder-of-outreachy/$', views.blog_2022_06_14_remembering_marina, name='2022-06-remembering-marina'),

    url(r'^privacy-policy/$', views.privacy_policy, name='privacy-policy'),
]
