import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.formats import date_format
import reversion
import unittest

from home import models
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InitialApplicationPrivacyTestCase(TestCase):

    def create_initial_application(self, current_round):
        with reversion.create_revision():
            applicant_approval = factories.ApplicantApprovalFactory(
                    approval_status=models.ApprovalStatus.PENDING,
                    application_round=current_round,
                    )
            models.BarriersToParticipation(
                    applicant=applicant_approval,
                    country_living_in_during_internship="Sensitive info - country",
                    country_living_in_during_internship_code="42",
                    underrepresentation="Sensitive info - underrepresented groups",
                    lacking_representation="Sensitive info - lack of representation in education",
                    systemic_bias="Sensitive info - educational bias",
                    employment_bias="Sensitive info - employment bias",
                    ).save()
        return applicant_approval

    def create_applicant_reviewer(self, current_round, approval_status):
        reviewer = factories.ReviewerFactory()
        factories.ApplicationReviewerFactory(
            comrade=reviewer,
            reviewing_round=current_round,
            approval_status=approval_status,
        )
        return reviewer

    def check_essay_hidden_from_eligibility_results(self, applicant_approval):
        self.client.force_login(applicant_approval.applicant.account)
        response = self.client.get(reverse('eligibility-results'))
        self.assertNotContains(response, '<h4>Essay Questions</h4>', html=True)
        self.assertNotContains(response, '<h5 class="card-title">Q1. What country will you be living in during the internship?</h5>', html=True)
        self.assertNotContains(response, '<p class="card-text">Sensitive info - country</p>', html=True)
        self.assertNotContains(response, '<h5 class="card-title">Q2. Are you part of an underrepresented group (in the technology industry of the country listed above)? How are you underrepresented?</h5>', html=True)
        self.assertNotContains(response, '<p class="card-text">Sensitive info - underrepresented groups</p>', html=True)
        self.assertNotContains(response, '<h5 class="card-title">Q3. Does your learning environment have few people who share your identity or background? Please provide details.</h5>', html=True)
        self.assertNotContains(response, '<p class="card-text">Sensitive info - lack of representation in education</p>', html=True)
        self.assertNotContains(response, '<h5 class="card-title">Q4. What systemic bias or discrimination have you faced while building your skills?</h5>', html=True)
        self.assertNotContains(response, '<p class="card-text">Sensitive info - educational bias</p>', html=True)
        self.assertNotContains(response, '<h5 class="card-title">Q5. What systemic bias or discrimination would you face if you applied for a job in the technology industry of your country?</h5>', html=True)
        self.assertNotContains(response, '<p class="card-text">Sensitive info - employment bias</p>', html=True)
        self.client.logout()

    def check_essay_visible_on_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        self.assertContains(response, '<h2>Essay Answers</h2>', html=True)
        self.assertContains(response, '<div class="card-header">Q1. What country will you be living in during the internship?</div>', html=True)
        self.assertContains(response, 'Sensitive info - country')
        self.assertContains(response, '<div class="card-header">Q2. Are you part of an underrepresented group (in the technology industry of the country listed above)? How are you underrepresented?</div>', html=True)
        self.assertContains(response, 'Sensitive info - underrepresented groups')
        self.assertContains(response, '<div class="card-header">Q3. Does your learning environment have few people who share your identity or background? Please provide details.</div>', html=True)
        self.assertContains(response, 'Sensitive info - lack of representation in education')
        self.assertContains(response, '<div class="card-header">Q4. What systemic bias or discrimination have you faced while building your skills?</div>', html=True)
        self.assertContains(response, 'Sensitive info - educational bias')
        self.assertContains(response, '<div class="card-header">Q5. What systemic bias or discrimination would you face if you applied for a job in the technology industry of your country?</div>', html=True)
        self.assertContains(response, 'Sensitive info - employment bias')

    def check_essay_hidden_from_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        self.assertContains(response, '<h2>Essay Answers</h2>', html=True)
        self.assertContains(response, '<p>The essay answers have been removed after initial application processing.</p>', html=True)
        self.assertNotContains(response, '<div class="card-header">Q1. What country will you be living in during the internship?</div>', html=True)
        self.assertNotContains(response, 'Sensitive info - country')
        self.assertNotContains(response, '<div class="card-header">Q2. Are you part of an underrepresented group (in the technology industry of the country listed above)? How are you underrepresented?</div>', html=True)
        self.assertNotContains(response, 'Sensitive info - underrepresented groups')
        self.assertNotContains(response, '<div class="card-header">Q3. Does your learning environment have few people who share your identity or background? Please provide details.</div>', html=True)
        self.assertNotContains(response, 'Sensitive info - lack of representation in education')
        self.assertNotContains(response, '<div class="card-header">Q4. What systemic bias or discrimination have you faced while building your skills?</div>', html=True)
        self.assertNotContains(response, 'Sensitive info - educational bias')
        self.assertNotContains(response, '<div class="card-header">Q5. What systemic bias or discrimination would you face if you applied for a job in the technology industry of your country?</div>', html=True)
        self.assertNotContains(response, 'Sensitive info - employment bias')


    def test_applicants_cannot_see_essays(self):
        """
        This tests that applicants cannot see their essay answers after the initial application was submitted.
        The round is in the initial application period.
        /eligibility-results/ should NOT show the essay answers.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant_approval = self.create_initial_application(current_round)

        self.check_essay_hidden_from_eligibility_results(applicant_approval)

    def test_approved_reviewers_can_see_essays(self):
        """
        This tests that approved applicant reviewers can see applicant essay answers after the initial application was submitted.
        The round is in the initial application period.
        /applicant-review-detail/ should show the essay answers.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant_approval = self.create_initial_application(current_round)

        reviewer = self.create_applicant_reviewer(current_round, models.ApprovalStatus.APPROVED)
        self.client.force_login(reviewer.account)

        self.check_essay_visible_on_application_review(account=reviewer.account, applicant_approval=applicant_approval)

    def test_essays_removed_on_processing(self):
        """
        This tests that approved applicant reviewers can see applicant essay answers after the initial application was submitted.
        The round is in the initial application period.
        /applicant-review-detail/ should show the essay answers.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')

        reviewer = self.create_applicant_reviewer(current_round, models.ApprovalStatus.APPROVED)
        # Only accounts with the Django staff privilege can approve initial applications
        # Organizers can both be staff and an initial application reviewer
        reviewer.account.is_staff = True
        reviewer.account.save()
        self.client.force_login(reviewer.account)

        for approval_status in [ models.ApprovalStatus.APPROVED, models.ApprovalStatus.REJECTED ]:
            with self.subTest(approval_status=approval_status):

                applicant_approval = self.create_initial_application(current_round)
                if approval_status == models.ApprovalStatus.APPROVED:
                    response = self.client.post(applicant_approval.get_approve_url())
                elif approval_status == models.ApprovalStatus.REJECTED:
                    response = self.client.post(applicant_approval.get_reject_url())

                self.assertRedirects(response, applicant_approval.get_preview_url())

                # Reload the object from the database after the invoked view modifies the database
                applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)
                self.assertEqual(applicant_approval.approval_status, approval_status)
                self.check_essay_hidden_from_application_review(account=reviewer.account, applicant_approval=applicant_approval)
                applicant_approval.delete()
