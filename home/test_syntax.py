"""
These tests don't check correct behavior, they just check that views don't
throw exceptions for any of the different types of visitors we might have. This
is a bare minimum level of testing that nonetheless would have caught a fair
number of bugs that we have shipped previously...
"""

from django.test import TestCase, override_settings
from django.urls import reverse

from . import factories, models


def include(prefix, paths):
    """
    By analogy with django.conf.urls.include, construct paths by adding a
    common prefix to each specified path suffix.
    """
    return [ prefix + path for path in paths ]

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SyntaxTestCase(TestCase):
    acceptable_status_codes = (
        # 2xx Success:
        200, # OK
        # reject all other 2xx status codes because they're for e.g. APIs

        # 3xx Redirection:
        # reject 300 Multiple Choices, nobody would know what to do with it
        301, # Moved Permanently (changes request method to GET)
        302, # Found (changes request method to GET, contrary to original spec)
        303, # See Other (changes request method to GET)
        # reject 304 Not Modified because this test doesn't send conditional requests
        # reject 305/306: obsolete proxy-related statuses
        307, # Temporary Redirect (preserves request method)
        308, # Permanent Redirect (preserves request method)

        # 4xx Client errors:
        # reject 400 Bad Request because we don't make bad requests :-P
        # reject 401 Unauthorized because we aren't using HTTP authentication
        # reject 402 Payment Required because, uh, yeah
        403, # Forbidden: visitor didn't have permission for this
        # reject 404 Not Found and 410 Gone because these tests should only generate valid URLs
        # reject 405 Method Not Allowed because we can't test POST-only views this way
        # reject all other 4xx status codes because they have more obscure uses

        # reject all 5xx Server errors because we don't want the server to have errors
    )

    def assertAcceptableStatus(self, path):
        response = self.client.get(path)
        self.assertIn(response.status_code, self.acceptable_status_codes)

    def testEachVisitorType(self):
        internselection = factories.InternSelectionFactory(active=True)
        project = internselection.project
        participation = project.project_round
        community = participation.community
        applicant = internselection.applicant.applicant.account
        mentor = internselection.mentors.get().mentor.account
        contribution = factories.ContributionFactory(
            round=participation.participating_round,
            applicant=internselection.applicant,
            project=project,
        )
        finalapplication = factories.FinalApplicationFactory(
            round=participation.participating_round,
            applicant=internselection.applicant,
            project=project,
        )
        coordinator = factories.CoordinatorApprovalFactory(
            approval_status=models.ApprovalStatus.APPROVED,
            community=community,
        ).coordinator.account
        reviewer = factories.ApplicationReviewerFactory(
            reviewing_round=participation.participating_round,
        ).comrade.account

        visitors = (
            ("no comrade", factories.UserFactory()),
            ("only comrade", factories.ComradeFactory().account),
            ("organizer", factories.ComradeFactory(account__is_staff=True).account),
            ("applicant", applicant),
            ("mentor", mentor),
            ("coordinator", coordinator),
            ("reviewer", reviewer),
        )

        # Some views expect that only one round will be in a particular phase
        # at a given time, and if we create multiple RoundPages without telling
        # the factory to space them out, that assumption will be violated. So
        # this .get() validates that we created exactly one; if it throws an
        # exception, that will count as a test error.
        current_round = models.RoundPage.objects.get()

        # from community_cfp_patterns:
        community_cfp_paths = [
            "/edit/",
            "/notify/",
            "/coordinator/preview/{}/".format(coordinator.username),
            "/coordinator/submit/",
            "/coordinator/submit/{}/".format(coordinator.username),
            "/coordinator/approve/{}/".format(coordinator.username),
            "/coordinator/reject/{}/".format(coordinator.username),
            "/coordinator/withdraw/{}/".format(coordinator.username),
            "/",
        ]

        round_community_project_paths = [
            "/intern-agreement/",
            # can't test POST-only view, AlumStanding
            "/final-application/{}/select/".format(applicant.username),
            "/final-application/{}/remove/".format(applicant.username),
            "/final-application/{}/resign/".format(applicant.username),
            "/final-application/{}/project-timeline/".format(applicant.username),
            "/mentor-contract-export/{}/".format(applicant.username),
            # can't test POST-only views, InternFund/InternApprove/FinalApplicationRate
            "/final-application/submit/",
            "/final-application/submit/{}/".format(applicant.username),
            "/final-application/approve/{}/".format(applicant.username),
            "/final-application/reject/{}/".format(applicant.username),
            "/final-application/withdraw/{}/".format(applicant.username),
            "/contributions/add/",
            "/contributions/{}/".format(contribution.pk),
            "/contributions/",
            "/applicants/",
            "/cfp/mentor/preview/{}/".format(mentor.username),
            "/cfp/mentor/submit/",
            "/cfp/mentor/submit/{}/".format(mentor.username),
            "/cfp/mentor/approve/{}/".format(mentor.username),
            "/cfp/mentor/reject/{}/".format(mentor.username),
            "/cfp/mentor/withdraw/{}/".format(mentor.username),
            "/cfp/skills/",
            "/cfp/channels/",
            "/cfp/",
        ]

        # This is buggy - mentors shouldn't be able to submit projects
        # after the intern announcement date, which is what the default
        # round date when you call InternSelectionFactory
        round_community_paths = [
            "/applicants/",
            "/submit-project/",
            "/submit-project/{}/".format(project.slug),
            "/approve-project/{}/".format(project.slug),
            "/reject-project/{}/".format(project.slug),
            "/withdraw-project/{}/".format(project.slug),
            #"/submit/",
            #"/approve/",
            #"/reject/",
            #"/withdraw/",
            "/",
        ] + include("/{}".format(project.slug), round_community_project_paths)

        round_paths = [
            "/contract-export/",
            "/initial-feedback-export/",
            "/initial-feedback-summary/",
            "/midpoint-feedback-summary/",
            "/email/deadline-review/",
            "/email/mentor-application-deadline-reminder/",
            "/email/mentor-intern-selection-reminder/",
            "/email/coordinator-intern-selection-reminder/",
            "/email/deadline-reminder/",
            "/email/application-period-ended/",
            "/email/contributor-deadline-reminder/",
            "/email/intern-welcome/",
            "/email/internship-week-1/",
            "/email/internship-week-3/",
            "/email/internship-week-5/",
            "/email/internship-week-7/",
            "/email/initial-feedback-instructions/",
            "/email/midpoint-feedback-instructions/",
            "/email/final-feedback-instructions/",
        ] + include("/communities/{}".format(community.slug), round_community_paths)

        paths = sum((
            [
                "/",
                "/communities/cfp/add/",
                "/communities/cfp/",
                "/intern-contract-export/",
                "/generic-intern-contract-export/",
                "/generic-mentor-contract-export/",
                "/alums/",
                "/dashboard/",
                "/dashboard/pending-applications/",
                "/dashboard/rejected-applications/",
                "/dashboard/approved-applications/",
                # can't test POST-only view, DeleteApplication
                "/dashboard/review-applications/{}/".format(applicant.username),
                "/dashboard/review-applications/update-comment/{}/".format(applicant.username),
                # our test ApplicantApproval is already approved; we can only test rejecting it
                "/dashboard/review-applications/reject/{}/".format(applicant.username),
                # can't test POST-only views, EssayRating/ChangeRedFlag/SetReviewOwner
                "/dashboard/feedback/mentor/initial/{}/".format(applicant.username),
                "/dashboard/feedback/intern/initial/",
                "/dashboard/feedback/mentor/midpoint/{}/".format(applicant.username),
                "/dashboard/feedback/intern/midpoint/",
                "/dashboard/trusted-volunteers/",
                "/eligibility/",
                # need to create BarriersToParticipation and SchoolInformation to test these two:
                #"/eligibility/essay-revision/{}/".format(applicant.username),
                #"/eligibility/school-revision/{}/".format(applicant.username),
                # can't test POST-only views, NotifyEssayNeedsUpdating/NotifySchoolInformationUpdating
                "/eligibility-results/",
                "/longitudinal-survey/2018-initiate/",
                "/longitudinal-survey/2018-completed/",
                # can't test AlumSurveyUpdate or survey_opt_out without a fake survey object
                "/account/",
                "/apply/project-selection/",
                "/past-projects/",
                "/apply/eligibility/",
                "/blog/{}/application-period-statistics/".format(current_round.slug),
                "/privacy-policy/",
            ],
            include("/communities/cfp/{}".format(community.slug), community_cfp_paths),
            include("/{}".format(current_round.slug), round_paths),
        ), [])

        for path in paths:
            with self.subTest(path=path):
                with self.subTest(visitor_type="unauthenticated"):
                    self.client.logout()
                    self.assertAcceptableStatus(path)

                for visitor_type, visitor in visitors:
                    with self.subTest(visitor_type=visitor_type):
                        self.client.force_login(visitor)
                        self.assertAcceptableStatus(path)
