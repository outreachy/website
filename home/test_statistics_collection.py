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
class StatisticsCollectionTestCase(TestCase):

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
                transgender=False,
                genderqueer=False,
                man=False,
                woman=False,
                demi_boy=False,
                demi_girl=False,
                trans_masculine=False,
                trans_feminine=False,
                non_binary=False,
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

    def nullify_gender(self, applicant_approval):
        for gender in [f for f in applicant_approval.applicantgenderidentity._meta.get_fields() if f.get_internal_type() == 'BooleanField']:
            # unset this gender identity
            setattr(applicant_approval, gender, False)

    def setup_internship_round_and_reviewer(self):
        current_round = factories.RoundPageFactory(start_from='initial_applications_open')

        reviewer = self.create_applicant_reviewer(current_round, models.ApprovalStatus.APPROVED)
        # Only accounts with the Django staff privilege can approve initial applications
        # Organizers can both be staff and an initial application reviewer
        reviewer.account.is_staff = True
        reviewer.account.save()
        self.client.force_login(reviewer.account)
        return (current_round, reviewer)

    def test_collection_of_non_binary_gender_identity(self):
        """
        This tests that statistics about non-binary applicants are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()

        # Loop through all non-binary genders, creating one ApplicantApproval for each
        # Ensure that non-binary people are counted in the round's aggregate statistics
        for gender in [f.attname for f in models.ApplicantGenderIdentity._meta.get_fields() if f.get_internal_type() == 'BooleanField' and f.name != 'prefer_not_to_say' and f.name != 'man' and f.name != 'woman' and f.name != 'trans_masculine' and f.name != 'trans_feminine' and f.name != 'transgender' and f.name != 'genderqueer']:
            with self.subTest(gender=gender):
                applicant_approval = self.create_initial_application(current_round)
                setattr(applicant_approval.applicantgenderidentity, gender, True)
                applicant_approval.applicantgenderidentity.save()
                self.assertTrue(getattr(applicant_approval.applicantgenderidentity, gender))

                # Get the current count of non-binary applicants
                try:
                    stats = models.StatisticGenderDemographics.objects.get(
                            internship_round=current_round)
                    counted_non_binary_people = stats.total_non_binary_people
                except models.StatisticGenderDemographics.DoesNotExist:
                    counted_non_binary_people = 0

                # Approve the initial application, which does not collect statistics
                response = self.client.post(applicant_approval.get_approve_url())
                # Reload the objects from the database after the invoked view modifies the database
                applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

                # Manually collect statistics and purge essay
                applicant_approval.collect_statistics()
                applicant_approval.purge_sensitive_data()

                self.assertTrue(applicant_approval.collected_statistics)
                stats = models.StatisticGenderDemographics.objects.get(
                        internship_round=current_round)


                self.assertEquals(0, stats.total_transgender_people)
                self.assertEquals(0, stats.total_genderqueer_people)
                self.assertEquals(0, stats.total_men)
                self.assertEquals(0, stats.total_trans_masculine_people)
                self.assertEquals(0, stats.total_women)
                self.assertEquals(0, stats.total_trans_feminine_people)
                self.assertEquals(counted_non_binary_people + 1, stats.total_non_binary_people)
                self.assertEquals(0, stats.total_who_self_identified_gender)

    def test_collection_of_statistics_for_non_binary_applicant(self):
        """
        This tests that statistics about an applicant with multiple gender identities are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)
        gender_identity = models.ApplicantGenderIdentity.objects.get(
                applicant=applicant_approval,
                )

        # AMAB non-binary people exist!
        gender_identity.genderqueer = True
        gender_identity.man = True
        gender_identity.non_binary = True
        gender_identity.demiboy = True
        gender_identity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked view modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        self.assertTrue(applicant_approval.collected_statistics)
        stats = models.StatisticGenderDemographics.objects.get(
                internship_round=current_round)

        self.assertEquals(0, stats.total_transgender_people)
        self.assertEquals(1, stats.total_genderqueer_people)
        self.assertEquals(1, stats.total_men)
        self.assertEquals(0, stats.total_trans_masculine_people)
        self.assertEquals(0, stats.total_women)
        self.assertEquals(0, stats.total_trans_feminine_people)
        self.assertEquals(1, stats.total_non_binary_people)

    def test_collection_of_statistics_for_transgender_woman_applicant(self):
        """
        This tests that statistics about an applicant with multiple gender identities are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)
        gender_identity = models.ApplicantGenderIdentity.objects.get(
                applicant=applicant_approval,
                )

        # Trans women are women!
        gender_identity.transgender = True
        gender_identity.woman = True
        gender_identity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked view modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()
        
        self.assertTrue(applicant_approval.collected_statistics)
        stats = models.StatisticGenderDemographics.objects.get(
                internship_round=current_round)

        self.assertEquals(1, stats.total_transgender_people)
        self.assertEquals(0, stats.total_genderqueer_people)
        self.assertEquals(0, stats.total_men)
        self.assertEquals(0, stats.total_trans_masculine_people)
        self.assertEquals(1, stats.total_women)
        self.assertEquals(0, stats.total_trans_feminine_people)
        self.assertEquals(0, stats.total_non_binary_people)
        self.assertEquals(0, stats.total_who_self_identified_gender)

    def test_collection_of_statistics_for_trans_masculine_agender_person(self):
        """
        This tests that statistics about an applicant with multiple gender identities are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)
        gender_identity = models.ApplicantGenderIdentity.objects.get(
                applicant=applicant_approval,
                )

        gender_identity.transgender = True
        gender_identity.trans_masculine = True
        gender_identity.agender = True
        gender_identity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked view modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        self.assertTrue(applicant_approval.collected_statistics)
        stats = models.StatisticGenderDemographics.objects.get(
                internship_round=current_round)

        self.assertEquals(1, stats.total_transgender_people)
        self.assertEquals(0, stats.total_genderqueer_people)
        self.assertEquals(0, stats.total_men)
        self.assertEquals(1, stats.total_trans_masculine_people)
        self.assertEquals(0, stats.total_women)
        self.assertEquals(0, stats.total_trans_feminine_people)
        self.assertEquals(1, stats.total_non_binary_people)
        self.assertEquals(0, stats.total_who_self_identified_gender)

    def test_collection_of_statistics_for_trans_feminine_mavrique(self):
        """
        This tests that statistics about an applicant with multiple gender identities are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)
        gender_identity = models.ApplicantGenderIdentity.objects.get(
                applicant=applicant_approval,
                )

        gender_identity.transgender = True
        gender_identity.trans_feminine = True
        gender_identity.mavrique = True
        gender_identity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked view modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        self.assertTrue(applicant_approval.collected_statistics)
        stats = models.StatisticGenderDemographics.objects.get(
                internship_round=current_round)

        self.assertEquals(1, stats.total_transgender_people)
        self.assertEquals(0, stats.total_genderqueer_people)
        self.assertEquals(0, stats.total_men)
        self.assertEquals(0, stats.total_trans_masculine_people)
        self.assertEquals(0, stats.total_women)
        self.assertEquals(1, stats.total_trans_feminine_people)
        self.assertEquals(1, stats.total_non_binary_people)
        self.assertEquals(0, stats.total_who_self_identified_gender)

    def test_collection_of_statistics_twice(self):
        """
        This tests that statistics about an applicant with multiple gender identities are collected correctly.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)
        gender_identity = models.ApplicantGenderIdentity.objects.get(
                applicant=applicant_approval,
                )

        gender_identity.transgender = True
        gender_identity.woman = True
        gender_identity.trans_feminine = True
        gender_identity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()
        self.assertTrue(applicant_approval.collected_statistics)

        # Reject the initial application, which should NOT collect statistics
        response = self.client.post(applicant_approval.get_reject_url())
        # Note: this actually sometimes happens,
        # when a staff accidentally clicks 'approve' instead of 'reject'

        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)
        self.assertTrue(applicant_approval.collected_statistics)
        stats = models.StatisticGenderDemographics.objects.get(
                internship_round=current_round)

        self.assertEquals(1, stats.total_transgender_people)
        self.assertEquals(0, stats.total_genderqueer_people)
        self.assertEquals(0, stats.total_men)
        self.assertEquals(0, stats.total_trans_masculine_people)
        self.assertEquals(1, stats.total_women)
        self.assertEquals(1, stats.total_trans_feminine_people)
        self.assertEquals(0, stats.total_non_binary_people)
        self.assertEquals(0, stats.total_who_self_identified_gender)

        stats = models.StatisticTotalApplied.objects.get(
                internship_round=current_round)

        self.assertEquals(1, stats.total_applicants)
        # This person was approved and then rejected,
        # but we only collect statistics the first time,
        # so they will count as "approved"
        self.assertEquals(1, stats.total_approved)
        self.assertEquals(0, stats.total_pending)
        self.assertEquals(0, stats.total_rejected)
        self.assertEquals(0, stats.total_withdrawn)

    def test_collection_of_statistics_for_applicant_who_is_not_american_citizen(self):
        """
        This tests collection of race and ethnicity statistics about an applicant who is not an American
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)

        payment_eligibility = models.PaymentEligibility.objects.get(
                applicant=applicant_approval,
                )
        payment_eligibility.us_national_or_permanent_resident = False
        payment_eligibility.save()

        # Applicants who are not U.S. citizens
        # will not have race and ethnicity information collected
        # by the initial application form
        models.ApplicantRaceEthnicityInformation.objects.get(
                applicant=applicant_approval,
                ).delete()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        try:
            stats = models.StatisticAmericanDemographics.objects.get(
                    internship_round=current_round,
                    )
            self.assertFalse(True)
        except:
            pass

    def test_collection_of_statistics_for_american_applicant_who_is_not_bipoc(self):
        """
        This tests collection of race and ethnicity statistics about an applicant who is an American and is not any of the following races or ethnicities: Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)

        race_and_ethnicity = models.ApplicantRaceEthnicityInformation.objects.get(
                applicant=applicant_approval,
                )
        race_and_ethnicity.us_resident_demographics = False
        race_and_ethnicity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        try:
            stats = models.StatisticAmericanDemographics.objects.get(
                    internship_round=current_round,
                    )
        except:
            self.assertFalse(True)

        self.assertEquals(1, stats.total_approved_american_applicants)
        self.assertEquals(0, stats.total_approved_american_bipoc)

    def test_collection_of_statistics_for_american_applicant_who_is_bipoc(self):
        """
        This tests collection of race and ethnicity statistics about an applicant who is an American and is any of the following races or ethnicities: Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)

        race_and_ethnicity = models.ApplicantRaceEthnicityInformation.objects.get(
                applicant=applicant_approval,
                )
        race_and_ethnicity.us_resident_demographics = True
        race_and_ethnicity.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        try:
            stats = models.StatisticAmericanDemographics.objects.get(
                    internship_round=current_round,
                    )
        except:
            self.assertFalse(True)

        self.assertEquals(1, stats.total_approved_american_applicants)
        self.assertEquals(1, stats.total_approved_american_bipoc)

    def test_collection_of_statistics_for_one_country(self):
        """
        This tests collection of data about what country applicants will be living in during the internship.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()
        applicant_approval = self.create_initial_application(current_round)

        essays = models.BarriersToParticipation.objects.get(
                applicant=applicant_approval,
                )
        essays.country_living_in_during_internship = 'India'
        essays.country_living_in_during_internship_code = 'IN'
        essays.save()

        # Approve the initial application, which does not collect statistics
        response = self.client.post(applicant_approval.get_approve_url())
        # Reload the objects from the database after the invoked views modifies the database
        applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

        # Manually collect statistics and purge essay
        applicant_approval.collect_statistics()
        applicant_approval.purge_sensitive_data()

        try:
            models.StatisticApplicantCountry.objects.get(
                    internship_round=current_round,
                    country_living_in_during_internship=essays.country_living_in_during_internship,
                    country_living_in_during_internship_code=essays.country_living_in_during_internship_code,
                    total_applicants=1,
                    )
        except:
            self.assertFalse(True)

    def test_collection_of_statistics_for_multiple_applicants_from_same_country(self):
        """
        This tests collection of data about what country applicants will be living in during the internship.
        """
        current_round, reviewer = self.setup_internship_round_and_reviewer()

        for i in range(3):
            applicant_approval = self.create_initial_application(current_round)

            essays = models.BarriersToParticipation.objects.get(
                    applicant=applicant_approval,
                    )
            essays.country_living_in_during_internship = 'India'
            essays.country_living_in_during_internship_code = 'IN'
            essays.save()

            # Approve the initial application, which does not collect statistics
            response = self.client.post(applicant_approval.get_approve_url())
            # Reload the objects from the database after the invoked views modifies the database
            applicant_approval = models.ApplicantApproval.objects.get(pk=applicant_approval.pk)

            # Manually collect statistics and purge essay
            applicant_approval.collect_statistics()
            applicant_approval.purge_sensitive_data()

        try:
            models.StatisticApplicantCountry.objects.get(
                    internship_round=current_round,
                    country_living_in_during_internship=essays.country_living_in_during_internship,
                    country_living_in_during_internship_code=essays.country_living_in_during_internship_code,
                    total_applicants=3,
                    )
        except:
            self.assertFalse(True)
