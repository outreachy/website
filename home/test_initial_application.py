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
    #  - /apply/project-selection/ - should not display detailed links to the project/community pages
    #  - community landing page - should not display details about the community or projects until contributions_open
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
        /eligibility-results/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='GENERAL', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertContains(response, '<li>You may have already participated in Google Summer of Code or a previous Outreachy round.</li>', html=True)
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
        /eligibility-results/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='TIME', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('eligibility-results'))
        self.assertContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertContains(response, '<p>After reviewing your time commitments, we have determined you do not meet our minimum free time criteria.</p>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    @unittest.expectedFailure
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
        self.assertContains(response, '<h1>Your Initial Application is Under Review</h1>', html=True)
        self.assertNotContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertNotContains(response, '<p>The Outreachy organizers have been reviewing your initial application, including your essay questions.</p>', html=True)
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
        self.assertNotContains(response, '<h1>Your Initial Application is Under Review</h1>', html=True)
        self.assertContains(response, '<h1>Initial application is not approved</h1>', html=True)
        self.assertContains(response, '<p>The Outreachy organizers have been reviewing your initial application, including your essay questions.</p>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    @unittest.expectedFailure
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
        self.assertContains(response, '<h1>Your Initial Application is Under Review</h1>', html=True)
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
        self.assertNotContains(response, '<h1>Your Initial Application is Under Review</h1>', html=True)
        self.assertContains(response, '<h1>Initial application approved for Outreachy</h1>', html=True)
        self.assertEqual(response.status_code, 200)

    # Applicant prompt tests - use dasboard, since that's the page with the least other content
    def test_applicant_prompts_general_rejection(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'GENERAL' - they don't meet our eligibility rules
        The round is in the initial application period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='GENERAL', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
        self.assertEqual(response.status_code, 200)

    def test_applicant_prompts_time_rejection(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'TIME' - they don't have 49 out of 91 days free from full-time commitments.
        The round is in the initial application period.
        /dashboard/ should show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='TIME', application_round=current_round)
        self.client.force_login(applicant.applicant.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<div class="card-header text-white bg-warning">Initial Application Not Approved</div>', html=True)
        self.assertEqual(response.status_code, 200)

    # FIXME - this test shouldn't fail if the new code works right
    @unittest.expectedFailure
    def test_applicant_prompts_alignment_rejection_before_contributions_open(self):
        """
        This tests that the initial application results.
        The applicant is rejected because of 'ALIGN' - mis-alignment with Outreachy program goals.
        The round is in the initial application period.
        /dashboard/ should NOT show the person is rejected.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant = factories.ApplicantApprovalFactory(approval_status=models.ApprovalStatus.REJECTED, reason_denied='ALIGN', application_round=current_round)
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

    # FIXME - this test shouldn't fail if the new code works right
    @unittest.expectedFailure
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
