import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.formats import date_format
import unittest

from home import models
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProjectSubmissionTestCase(TestCase):

    # ----- eligibility information page tests (/apply/eligibility/) ----- #

    def test_initial_application_marked_closed(self):
        """
        This tests how the website works before we start accepting initial applications
         - Create a new RoundPage for the upcoming round where initial_applications_open has not passed
         - /apply/eligibility/ should not have a button to submit an application
         - it should not have a prompt to submit an application
         - it should have a prompt saying initial applications are currently closed
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open', days_after_today=1)

        response = self.client.get(reverse('eligibility-information'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p>The application system for Outreachy internships is currently closed. The application system will be available when the application period opens on {} at 4pm UTC. Initial applications are due on {} 4pm UTC.</p>'.format(date_format(current_round.initial_applications_open), date_format(current_round.initial_applications_close)), html=True)
    def test_initial_application_form_closed_before_period(self):
        """
        This tests that the initial application form is closed before the initial applications open
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open', days_after_today=1)
        applicant = factories.ComradeFactory()
        self.client.force_login(applicant.account)

        response = self.client.get(reverse('eligibility'))
        self.assertEqual(response.status_code, 403)

    # ----- initial application results page tests (/eligibility-results/) ----- #

    def test_initial_application_form_open_during_period(self):
        """
        This tests that the initial application form is open during the initial application period
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ComradeFactory()
        self.client.force_login(applicant.account)

        response = self.client.get(reverse('eligibility'))
        self.assertEqual(response.status_code, 200)

    def test_initial_application_form_closed_after_period(self):
        """
        This tests that the initial application form is closed after the initial application deadline
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_close')
        applicant = factories.ComradeFactory()
        self.client.force_login(applicant.account)

        response = self.client.get(reverse('eligibility'))
        self.assertEqual(response.status_code, 403)

    # Email behavior to test:
    # - do not send any email on initial application status change
    # - new function will send email to all approved applicants at once
    #
    # Pages to test:
    #  - /apply/eligibility/ - shouldn't have a button to submit an application after they've already done so
    #  - /dashboard/
    #    - should not display any prompts to make a contribution or talk about the initial application status
    #    - should display a prompt to read the applicant guide - until interns are announced?
    #  - shouldn't be able to hit the contribution recording page until contributions_open
    #  - shouldn't be able to hit the final application page until contributions_open

    def test_initial_application_results_general_rejection(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
        The round is in the initial application period.
        /eligibility-results/ should not show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='GENERAL', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertNotContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertNotContains(response, '<li>You may have already participated in Google Summer of Code or a previous Outreachy round.</li>', html=True)
        self.assertEqual(response.status_code, 200)

    # Implication:
    #  - Sometimes when an Outreachy organizer notices the person put in the wrong dates for their school terms,
    #    they will correct the dates on the initial application.
    #  - This may mean they get rejected mark as being rejected because of TIME
    #  - They won't see this on their initial application results at first
    #  - Later, when they check it during the initial application period, they may notice it.
    #  - This could be slightly confusing for them, but it's necessary
    def test_initial_application_results_time_rejection(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
        The round is in the initial application period.
        /eligibility-results/ should not show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='TIME', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertNotContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertNotContains(response, '<p>After reviewing your time commitments, we have determined you do not meet our minimum free time criteria.</p>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    def test_initial_application_results_alignment_rejection_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        /eligibility-results/ should NOT show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='ALIGN', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertNotContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertNotContains(response, '<p>Outreachy reviewed your essay answers. We found that your essays did not sufficiently explain why your application is aligned with Outreachy program goals.</p>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_initial_application_results_alignment_rejection_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the contribution application period.
        /eligibility-results/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='ALIGN', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertNotContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertContains(response, '<p>Outreachy reviewed your essay answers. We found that your essays did not sufficiently explain why your application is aligned with Outreachy program goals.</p>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_initial_application_results_pending_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant was not reviewed, either because they didn't answer our emails, or we didn't have time to review all applications.
        The round is in the contribution application period.
        /eligibility-results/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.PENDING, application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertNotContains(response, '<h1>Your Initial Application is Under Review</h1>', html=True)
        self.assertContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    def test_initial_application_results_approved_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the initial application period.
        /eligibility-results/ should NOT show the person is approved.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertNotContains(response, '<h1>Initial application approved for Outreachy</h1>', html=True)
        self.assertEqual(response.status_code, 200)

    # - Applicants accepted should be able to see their application once the contribution period opens
    def test_initial_application_results_approved_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the contribution period.
        /eligibility-results/ should show the person is approved.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertNotContains(response, '<h1>Your initial application is under review</h1>', html=True)
        self.assertContains(response, '<h1>Initial application approved for Outreachy</h1>', html=True)
        self.assertEqual(response.status_code, 200)

    # ----- applicant prompt snippet tests (various pages) ----- #

    def test_applicant_prompts_alignment_time_general_rejection_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        /dashboard/ should NOT show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=current_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('dashboard'))
                self.assertNotContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
                self.assertContains(response, '<div class="card-header text-white bg-warning">Outreachy Initial Application Under Review</div>', html=True)
                self.assertEqual(response.status_code, 200)

    def test_applicant_prompts_alignment_rejection_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the contribution period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='ALIGN', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_applicant_prompts_general_rejection_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
        The round is in the initial application period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='GENERAL', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_applicant_prompts_time_rejection_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
        The round is in the initial application period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='TIME', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    def test_applicant_prompts_approved_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the initial application period.
        /dashboard/ should NOT show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, '<div class="card-header text-white bg-warning">A Contribution is Required</div>', html=True)
        self.assertContains(response, '<div class="card-header text-white bg-warning">Outreachy Initial Application Under Review</div>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_applicant_prompts_approved_after_contributions_open(self):
        """
        This tests the applicant prompts in combination with the initial application results.
        The applicant is approved.
        The round is in the contribution period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='contributions_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">A Contribution is Required</div>', html=True)
        self.assertEqual(response.status_code, 200)

    # ----- project list page tests (/apply/project-selection) ----- #

    def setup_approved_project_approved_community(self, start_from):
        current_round = factories.RoundPageFactory(start_from=start_from)
        project = factories.ProjectFactory(
                approval_status=models.ApprovalStatus.APPROVED,
                project_round__participating_round=current_round,
                project_round__approval_status=models.ApprovalStatus.APPROVED,
                project_round__community__name='Debian',
                project_round__community__slug='debian',
                contribution_tasks='<p>Just pick something from the issue tracker.</p>',
                )
        sponsorship = factories.SponsorshipFactory(participation=project.project_round,
                name='Software in the Public Interest - Debian',
                amount=13000)
        return project

    def test_project_list_not_logged_in(self):
        """
        Applicant is not logged in.
        They shouldn't be able to see links to community pages or project details.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        response = self.client.get(reverse('project-selection'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h4 id="debian">Debian - 2 interns</h4>', html=True)
        self.assertContains(response, 'Project details are hidden.')
        self.assertNotContains(response, '<a href="{}">Debian community landing page</a>'.format(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug})), html=True)
        self.assertNotContains(response, '<a href="{}#{}">{}</a>'.format(project.project_round.get_absolute_url(), project.slug, project.short_title), html=True)

    def test_project_list_general_time_align_rejection_before_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        They shouldn't be able to see links to community pages or project details.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('project-selection'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<h4 id="debian">Debian - 2 interns</h4>', html=True)
                self.assertContains(response, 'Project details are hidden.')
                self.assertNotContains(response, '<a href="{}">Debian community landing page</a>'.format(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug})), html=True)
                self.assertNotContains(response, '<a href="{}#{}">{}</a>'.format(project.project_round.get_absolute_url(), project.slug, project.short_title), html=True)

    def test_project_list_general_time_align_rejection_after_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        They shouldn't be able to see links to community pages or project details.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('project-selection'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<h4 id="debian">Debian - 2 interns</h4>', html=True)
                self.assertContains(response, 'Project details are hidden.')
                self.assertNotContains(response, '<a href="{}">Debian community landing page</a>'.format(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug})), html=True)
                self.assertNotContains(response, '<a href="{}#{}">{}</a>'.format(project.project_round.get_absolute_url(), project.slug, project.short_title), html=True)

    # FIXME - this test shouldn't fail if the new code works right
    def test_project_list_approved_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the initial application period.
        They shouldn't be able to see links to community pages or project details.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('project-selection'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h4 id="debian">Debian - 2 interns</h4>', html=True)
        self.assertContains(response, 'Project details are hidden.')
        self.assertNotContains(response, '<a href="{}">Debian community landing page</a>'.format(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug})), html=True)
        self.assertNotContains(response, '<a href="{}#{}">{}</a>'.format(project.project_round.get_absolute_url(), project.slug, project.short_title), html=True)

    def test_project_list_approved_after_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the initial application period.
        They shouldn't be able to see links to community pages or project details.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('project-selection'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h4 id="debian">Debian - 2 interns</h4>', html=True)
        self.assertNotContains(response, 'Project details are hidden.')
        self.assertContains(response, '<a href="{}">Debian community landing page</a>'.format(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug})), html=True)
        self.assertContains(response, '<a href="{}#{}">{}</a>'.format(project.project_round.get_absolute_url(), project.slug, project.short_title), html=True)


    # ----- community landing page tests (/apply/eligibility/) ----- #

    def test_community_landing_general_time_align_rejection_before_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        They shouldn't be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response,
                        '<p>If you are an Outreachy applicant, this information will be available once the Outreachy contribution period starts on {} at 4pm UTC. You can sign up for an email notification when the round opens by <a href="https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce">subscribing to the Outreachy announcements mailing list</a>.</p>'.format(date_format(project.project_round.participating_round.contributions_open)),
                        html=True)
                self.assertNotContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
                self.assertNotContains(response, '<h1>Open Projects</h1>', html=True)
                self.assertNotContains(response, '<div class="card border" id="debian-{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<hr id="{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    # FIXME - this test shouldn't fail if the new code works right
    # (Technically this isn't a failure - the headings are there, but the project content is missing.
    # This still meets the goal of making sure rejected applicants can't contact mentors,
    # but it could use some UX improvements.)
    def test_community_landing_general_time_align_rejection_after_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the contribution period.
        They shouldn't be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response,
                        '<p>This information is only available to applicants who have their initial application approved. Check your <a href="{}">initial application results</a> for more details.</p>'.format(reverse('eligibility-results')),
                        html=True)
                self.assertNotContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
                self.assertNotContains(response, '<h1>Open Projects</h1>', html=True)
                self.assertNotContains(response, '<div class="card border" id="debian-{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<hr id="{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    def test_community_landing_pending_after_contribution_opens(self):
        """
        This tests that the initial application results.
        The applicant is pending because their application didn't get reviewed.
        The round is in the contribution period.
        They shouldn't be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.PENDING, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                '<p>This information is only available to applicants who have their initial application approved. Check your <a href="{}">initial application results</a> for more details.</p>'.format(reverse('eligibility-results')),
                html=True)
        self.assertNotContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
        self.assertNotContains(response, '<h1>Open Projects</h1>', html=True)
        self.assertNotContains(response, '<div class="card border" id="debian-{}">'.format(project.slug), html=True)
        self.assertNotContains(response, '<hr id="{}">'.format(project.slug), html=True)
        self.assertNotContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    # FIXME - this test shouldn't fail if the new code works right
    # (Technically this isn't a failure - the headings are there, but the project content is missing.
    # This still meets the goal of making sure rejected applicants can't contact mentors,
    # but it could use some UX improvements.)
    def test_community_landing_pending_after_contribution_opens(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the contribution period.
        They should be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.PENDING, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response,
                '<p>If you are an Outreachy applicant, this information will be available once the Outreachy contribution period starts on {} at 4pm UTC. You can sign up for an email notification when the round opens by <a href="https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce">subscribing to the Outreachy announcements mailing list</a>.</p>'.format(date_format(project.project_round.participating_round.contributions_open)),
                html=True)
        self.assertNotContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
        self.assertNotContains(response, '<h1>Open Projects</h1>', html=True)
        self.assertNotContains(response, '<hr id="{}">'.format(project.slug), html=True)
        self.assertNotContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    def test_community_landing_approved_and_pending_before_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is approved.
         - The applicant is pending.
        The round is in the initial application period.
        They shouldn't be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        for approval_status in [models.ApprovalStatus.APPROVED, models.ApprovalStatus.PENDING, ]:
            with self.subTest(approval_status=approval_status):
                applicant = factories.ApplicantApprovalFactory(approval_status=approval_status, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response,
                        '<p>If you are an Outreachy applicant, this information will be available once the Outreachy contribution period starts on {} at 4pm UTC. You can sign up for an email notification when the round opens by <a href="https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce">subscribing to the Outreachy announcements mailing list</a>.</p>'.format(date_format(project.project_round.participating_round.contributions_open)),
                        html=True)
                self.assertNotContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
                self.assertNotContains(response, '<h1>Open Projects</h1>', html=True)
                self.assertNotContains(response, '<div class="card border" id="{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<hr id="{}">'.format(project.slug), html=True)
                self.assertNotContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    def test_community_landing_approved_after_contribution_opens(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the contribution period.
        They should be able to see projects on the community landing page.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('community-landing', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response,
                '<p>If you are an Outreachy applicant, this information will be available once the Outreachy contribution period starts on {} at 4pm UTC. You can sign up for an email notification when the round opens by <a href="https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce">subscribing to the Outreachy announcements mailing list</a>.</p>'.format(date_format(project.project_round.participating_round.contributions_open)),
                html=True)
        self.assertContains(response, '<h1>Outreachy Internships with Debian</h1>', html=True)
        self.assertContains(response, '<h1>Open Projects</h1>', html=True)
        self.assertContains(response, '<hr id="{}">'.format(project.slug), html=True)
        self.assertContains(response, '<h2>{}</h2>'.format(project.short_title), html=True)

    # ----- contribution recording page tests ----- #
    def test_contribution_recording_general_time_align_rejection_before_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        They shouldn't be able to record a contribution.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('contributions-add', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug, 'project_slug': project.slug }))
                # If an applicant is still under review we direct back to the eligibility results page
                self.assertRedirects(response, reverse('eligibility-results'))

    def test_contribution_recording_general_time_align_rejection_after_contribution_opens(self):
        """
        This tests permissions based on initial application status and whether the round is in the initial application or contribution period.
        Subtests:
         - The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
         - The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
         - The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the contribution period.
        They shouldn't be able to record a contribution.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        for rejection_reason in ['GENERAL', 'TIME', 'ALIGN', ]:
            with self.subTest(rejection_reason=rejection_reason):
                applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied=rejection_reason, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('contributions-add', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug, 'project_slug': project.slug }))
                # If an applicant is still under review we direct back to the eligibility results page
                self.assertRedirects(response, reverse('eligibility-results'))

    # FIXME - this test shouldn't fail if the new code works right
    # approved case is failing
    def test_contribution_recording_approved_and_pending_before_contribution_opens(self):
        """
        This tests that the initial application results.
        Subtests:
         - The applicant is pending
         - The applicant is approved
        The round is in the initial application period.
        They should NOT be able to record a contribution.
        """
        project = self.setup_approved_project_approved_community('initial_applications_open')

        for approval_status in [models.ApprovalStatus.APPROVED, models.ApprovalStatus.PENDING, ]:
            with self.subTest(approval_status=approval_status):
                applicant = factories.ApplicantApprovalFactory(approval_status=approval_status, application_round=project.project_round.participating_round)
                self.client.force_login(applicant.applicant.account)

                response = self.client.get(reverse('contributions-add', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug, 'project_slug': project.slug }))
                # If an applicant is still under review we direct back to the eligibility results page
                self.assertRedirects(response, reverse('eligibility-results'))

    def test_contribution_recording_pending_after_contribution_opens(self):
        """
        This tests that the initial application results.
        The applicant is pending.
        The round is in the contribution period.
        They should NOT be able to record a contribution.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.PENDING, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('contributions-add', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug, 'project_slug': project.slug }))
        # If an applicant is still under review we direct back to the eligibility results page
        self.assertRedirects(response, reverse('eligibility-results'))

    def test_contribution_recording_approved_after_contribution_opens(self):
        """
        This tests that the initial application results.
        The applicant is approved.
        The round is in the contribution period.
        They should be able to record a contribution.
        """
        project = self.setup_approved_project_approved_community('contributions_open')

        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.APPROVED, application_round=project.project_round.participating_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('contributions-add', kwargs={'round_slug': project.project_round.participating_round.slug, 'community_slug': project.project_round.community.slug, 'project_slug': project.slug }))
        self.assertEqual(response.status_code, 200)
