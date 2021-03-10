import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.formats import date_format
import reversion
from reversion.models import Version, Revision
import unittest

from home import models
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InitialApplicationPrivacyTestCase(TestCase):

    def create_sensitive_info(self, applicant_approval):
        models.PaymentEligibility(
                applicant=applicant_approval,
                us_national_or_permanent_resident=True,
                living_in_us=True,
                ).save()
        models.BarriersToParticipation(
                applicant=applicant_approval,
                country_living_in_during_internship="Sensitive info - country",
                country_living_in_during_internship_code="42",
                underrepresentation="Sensitive info - underrepresented groups",
                lacking_representation="Sensitive info - lack of representation in education",
                systemic_bias="Sensitive info - educational bias",
                employment_bias="Sensitive info - employment bias",
                ).save()
        models.ApplicantRaceEthnicityInformation(
                applicant=applicant_approval,
                us_resident_demographics=True,
                ).save()
        models.ApplicantGenderIdentity(
                applicant=applicant_approval,
                transgender=True,
                genderqueer=True,
                man=False,
                woman=False,
                demi_boy=False,
                demi_girl=False,
                trans_masculine=False,
                trans_feminine=False,
                non_binary=True,
                demi_non_binary=False,
                genderflux=False,
                genderfluid=False,
                demi_genderfluid=False,
                demi_gender=False,
                bi_gender=False,
                tri_gender=False,
                multigender=False,
                pangender=False,
                maxigender=False,
                aporagender=False,
                intergender=False,
                mavrique=False,
                gender_confusion=False,
                gender_indifferent=False,
                graygender=False,
                agender=False,
                genderless=False,
                gender_neutral=False,
                neutrois=False,
                androgynous=False,
                androgyne=False,
                prefer_not_to_say=False,
                ).save()

    def create_initial_application(self, current_round):
        applicant_approval = factories.ApplicantApprovalFactory(
                approval_status=models.ApprovalStatus.PENDING,
                application_round=current_round,
                )
        self.create_sensitive_info(applicant_approval)
        return applicant_approval

    def create_applicant_reviewer(self, current_round, approval_status):
        reviewer = factories.ReviewerFactory()
        factories.ApplicationReviewerFactory(
            comrade=reviewer,
            reviewing_round=current_round,
            approval_status=approval_status,
        )
        return reviewer

    def create_essay_quality(self):
        return models.EssayQuality.objects.create(
                category='Category',
                description='essay quality description',
                )

    def create_essay_review(self, reviewer, applicant_approval, essay_quality):
        reviewer_approval = models.ApplicationReviewer.objects.get(
            comrade=reviewer,
            reviewing_round=applicant_approval.application_round,
        )
        models.InitialApplicationReview(
                application=applicant_approval,
                reviewer=reviewer_approval,
                essay_rating=models.InitialApplicationReview.UNCLEAR,
                ).save()
        applicant_approval.essay_qualities.add(essay_quality)

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

    def check_race_and_ethnicity_visible_on_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        if applicant_approval.applicantraceethnicityinformation and applicant_approval.applicantraceethnicityinformation.us_resident_demographics:
            self.assertContains(response, "<p>Racial or ethnic minority in the United States technology industry: <b>Yes</b>, they're Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander</p>", html=True)
        if applicant_approval.applicantraceethnicityinformation and not applicant_approval.applicantraceethnicityinformation.us_resident_demographics:
            self.assertContains(response, "<p>Racial or ethnic minority in the United States technology industry: <b>No</b>, they're not Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander.</p>", html=True)

    def check_race_and_ethnicity_hidden_from_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        self.assertNotContains(response, "<p>Racial or ethnic minority in the United States technology industry: <b>Yes</b>, they're Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander</p>", html=True)
        self.assertContains(response, "<p>Racial or ethnic minority in the United States technology industry: [Removed]</p>", html=True)

    def check_gender_identity_visible_on_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        if applicant_approval.applicantgenderidentity:
            self.assertContains(response, "<p>Gender identity: <b>{}</b></p>".format(applicant_approval.applicantgenderidentity.__str__()), html=True)

    def check_gender_identity_hidden_from_application_review(self, account, applicant_approval):
        response = self.client.get(applicant_approval.get_preview_url())
        self.assertContains(response, "<p>Gender identity: [Removed]</p>", html=True)


    def check_sensitive_data_removed_from_database(self, applicant_approval):
        try:
            data = models.ApplicantGenderIdentity.objects.get(applicant=applicant_approval)
            self.assertIsNone(data)
        except models.ApplicantGenderIdentity.DoesNotExist:
            pass

        try:
            data = models.ApplicantRaceEthnicityInformation.objects.get(applicant=applicant_approval)
            self.assertIsNone(data)
        except models.ApplicantRaceEthnicityInformation.DoesNotExist:
            pass

        try:
            data = models.BarriersToParticipation.objects.get(applicant=applicant_approval)
            self.assertIsNone(data)
        except models.BarriersToParticipation.DoesNotExist:
            pass

        self.assertEquals(models.InitialApplicationReview.objects.filter(application=applicant_approval).count(), 0)

    def test_initial_applications_objects_not_under_revision_control(self):
        for model in (models.ApplicantApproval, models.BarriersToParticipation, models.ApplicantGenderIdentity, models.ApplicantRaceEthnicityInformation, models.SchoolInformation):
            with self.subTest(model=model):
                try:
                    version_query = Version.objects.get_for_model(model)
                    self.assertFalse(True)
                except reversion.errors.RegistrationError:
                    pass


    def test_applicants_cannot_see_sensitive_data(self):
        """
        This tests that applicants cannot see their essay answers after the initial application was submitted.
        The round is in the initial application period.
        /eligibility-results/ should NOT show the essay answers.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        applicant_approval = self.create_initial_application(current_round)

        self.check_essay_hidden_from_eligibility_results(applicant_approval)

    def test_approved_reviewers_can_see_sensitive_data(self):
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
        self.check_race_and_ethnicity_visible_on_application_review(account=reviewer.account, applicant_approval=applicant_approval)
        self.check_gender_identity_visible_on_application_review(account=reviewer.account, applicant_approval=applicant_approval)

    def test_sensitive_data_removed_on_processing(self):
        """
        This tests that approved applicant reviewers can see applicant essay answers after the initial application was submitted.
        The round is in the initial application period.
        /applicant-review-detail/ should show the essay answers.
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')

        reviewer = self.create_applicant_reviewer(current_round, models.ApprovalStatus.APPROVED)
        essay_quality = self.create_essay_quality()

        # Only accounts with the Django staff privilege can approve initial applications
        # Organizers can both be staff and an initial application reviewer
        reviewer.account.is_staff = True
        reviewer.account.save()
        self.client.force_login(reviewer.account)

        for approval_status in [ models.ApprovalStatus.APPROVED, models.ApprovalStatus.REJECTED ]:
            with self.subTest(approval_status=approval_status):

                applicant_approval = self.create_initial_application(current_round)
                self.create_essay_review(reviewer, applicant_approval, essay_quality)

                if approval_status == models.ApprovalStatus.APPROVED:
                    response = self.client.post(applicant_approval.get_approve_url())
                    # Reload the object from the database after the invoked view modifies the database
                    applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

                    # Manually collect statistics and purge essay
                    applicant_approval.collect_statistics()
                    applicant_approval.purge_sensitive_data()
                elif approval_status == models.ApprovalStatus.REJECTED:
                    response = self.client.post(applicant_approval.get_reject_url())

                self.assertRedirects(response, applicant_approval.get_preview_url())

                # Reload the object from the database after the invoked view modifies the database
                applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)
                self.assertEqual(applicant_approval.approval_status, approval_status)
                self.check_sensitive_data_removed_from_database(applicant_approval)
                self.check_essay_hidden_from_application_review(account=reviewer.account, applicant_approval=applicant_approval)
                self.check_race_and_ethnicity_hidden_from_application_review(account=reviewer.account, applicant_approval=applicant_approval)
                self.check_gender_identity_hidden_from_application_review(account=reviewer.account, applicant_approval=applicant_approval)

                # Make sure all linked essay qualities have been cleared.
                # Empty lists (or empty query sets) evaluate to False.
                self.assertFalse(applicant_approval.essay_qualities.all())

                applicant_approval.delete()

                # Ensure the essay quality objects remain in the database,
                # even after the application that had a foreign key reference
                # to the essay quality gets deleted
                models.EssayQuality.objects.get(
                        category=essay_quality.category,
                        description=essay_quality.description,
                        )
