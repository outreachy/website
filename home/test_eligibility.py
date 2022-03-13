from datetime import date, timedelta
from django.test import TestCase, override_settings

from .factories import ApplicantFactory, RoundPageFactory
from .models import ApplicantApproval, ApprovalStatus, RoundPage, PromotionTracking
from .views import determine_eligibility, EligibilityUpdateView

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class EligibilityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.application_round = RoundPageFactory(
            start_from="initial_applications_open",
            minimum_days_free_for_students=42,
            minimum_days_free_for_non_students=49,
        )

    all_gender_identities = (
        'transgender',
        'genderqueer',
        'man',
        'woman',
        'demi_boy',
        'demi_girl',
        'trans_masculine',
        'trans_feminine',
        'non_binary',
        'demi_non_binary',
        'genderqueer',
        'genderflux',
        'genderfluid',
        'demi_genderfluid',
        'demi_gender',
        'bi_gender',
        'tri_gender',
        'multigender',
        'pangender',
        'maxigender',
        'aporagender',
        'intergender',
        'mavrique',
        'gender_confusion',
        'gender_indifferent',
        'graygender',
        'agender',
        'genderless',
        'gender_neutral',
        'neutrois',
        'androgynous',
        'androgyne',
        'prefer_not_to_say',
    )

    @staticmethod
    def approved_work_eligibility(**kwargs):
        defaults = {
            # these must be answered this way to get approved:
            'over_18': True,
            'student_visa_restrictions': False,
            'eligible_to_work': True,
            'under_export_control': False,
            'us_sanctioned_country': False,
        }
        defaults.update(kwargs)
        return ('Work Eligibility', defaults)

    @staticmethod
    def approved_payment_eligibility(**kwargs):
        defaults = {
            # these don't really impact anything
            'us_national_or_permanent_resident': False,
            'living_in_us': False,
        }
        defaults.update(kwargs)
        return ('Payment Eligibility', defaults)

    @staticmethod
    def approved_foss_experience(**kwargs):
        defaults = {
            # these must be answered this way to get approved:
            'gsoc_or_outreachy_internship': False,
            # these don't really impact anything but are needed because we set the RadioBooleanField widget
            'prior_contributor': False,
            'prior_paid_contributor': False,
        }
        defaults.update(kwargs)
        return ('Prior FOSS Experience', defaults)

    @staticmethod
    def usa_demographics(us_resident_demographics):
        return ('USA demographics', {'us_resident_demographics': us_resident_demographics})

    @classmethod
    def not_usa_demographics(cls):
        """
        Returns an iterator over situations where we want to ask
        an applicant additional details about their demographics.
        """
        yield ('non-US', (
            cls.approved_work_eligibility(),
            cls.approved_payment_eligibility(),
            cls.approved_foss_experience(),
            cls.gender_identity(),
            cls.barriers_to_participation(),
            cls.time_commitments(),
            cls.promotional(),
        ))

        condition = 'us_national_or_permanent_resident'
        # Test not being in one of the invited U.S. demographics
        yield (condition, (
            cls.approved_work_eligibility(),
            cls.approved_payment_eligibility(**{condition: True}),
            cls.approved_foss_experience(),
            cls.usa_demographics(False),
            cls.gender_identity(),
            cls.barriers_to_participation(),
            cls.time_commitments(),
            cls.promotional(),
        ))
        # Test being in one of the invited U.S. demographics
        yield (condition, (
            cls.approved_work_eligibility(),
            cls.approved_payment_eligibility(**{condition: True}),
            cls.approved_foss_experience(),
            cls.usa_demographics(True),
            cls.gender_identity(),
            cls.barriers_to_participation(),
            cls.time_commitments(),
            cls.promotional(),
        ))

    @classmethod
    def gender_identity(cls, *args, **kwargs):
        defaults = {
            gender: False
            for gender in cls.all_gender_identities
        }
        defaults['self_identify'] = ''
        for arg in args:
            defaults[arg] = True
        defaults.update(kwargs)
        return ('Gender Identity', defaults)

    @classmethod
    def barriers_to_participation(cls, **kwargs):
        defaults = {
            'country_living_in_during_internship': 'Dwendalian Empire',
            'country_living_in_during_internship_code': '00',
            'underrepresentation': 'Yes',
            'employment_bias': 'Yes',
            'lacking_representation': 'Yes',
            'systemic_bias': 'Yes',
        }
        defaults.update(kwargs)
        return ('Barriers-to-Participation', defaults)

    @staticmethod
    def time_commitments(*args):
        defaults = {
            'enrolled_as_student': False,
            'enrolled_as_noncollege_student': False,
            'employed': False,
            'contractor': False,
            'volunteer_time_commitments': False,
        }
        for arg in args:
            defaults[arg] = True
        return ('Time Commitments', defaults)

    @staticmethod
    def promotional(*args):
        defaults = {
            'spread_the_word': PromotionTracking.OTHER,
        }
        return ('Outreachy Promotional Information', defaults)

    def assertEligible(self, expected_status, expected_reason, *data):
        applicant = ApplicantFactory()
        self.client.force_login(applicant.account)

        data = dict(data)
        prefix = "eligibility_update_view"
        completed_steps = []

        response = self.client.get("/eligibility/")
        while response.status_code == 200:
            wizard = response.context["wizard"]

            errors = wizard["form"].errors
            if isinstance(errors, list):
                self.assertEqual(wizard["form"].non_form_errors(), [])
            else:
                errors = [errors]
            for error in errors:
                self.assertEqual(error, {})

            current_step = wizard["steps"].current
            self.assertNotIn(current_step, completed_steps)
            completed_steps.append(current_step)

            answers = {
                f"{current_step}-{k}": v
                for k, v in data[current_step].items()
            }
            answers[f"{prefix}-current_step"] = current_step

            response = self.client.post("/eligibility/", answers)

        self.assertRedirects(response, "/eligibility-results/")
        self.assertEqual(set(data.keys()), set(completed_steps))

        result = applicant.applicantapproval_set.get()
        self.assertEqual(result.approval_status, expected_status)
        self.assertEqual(result.reason_denied, expected_reason)

    def test_saving_country_information(self):
        self.assertEligible(
                ApprovalStatus.PENDING,
                'ESSAY',
                self.approved_work_eligibility(),
                self.approved_payment_eligibility(),
                self.approved_foss_experience(),
                self.gender_identity(self.all_gender_identities[0]),
                self.barriers_to_participation(),
                self.time_commitments(),
                self.promotional(),
                )
        application = ApplicantApproval.objects.get()

        # Check that the country information
        # in BarriersToParticipation is copied to ApplicantApproval
        self.assertEqual(application.initial_application_country_living_in_during_internship, 'Dwendalian Empire')
        self.assertEqual(application.initial_application_country_living_in_during_internship_code, '00')

        # Check that collecting statistics and purging data
        # still leaves the country information in the ApplicantApproval object
        application.collect_statistics()
        application.purge_sensitive_data()
        self.assertEqual(application.initial_application_country_living_in_during_internship, 'Dwendalian Empire')
        self.assertEqual(application.initial_application_country_living_in_during_internship_code, '00')

    def test_reject_general(self):
        reject_if = (
            ('over_18', False),
            ('eligible_to_work', False),
            ('under_export_control', True),
        )
        # If any of the above are set, it shouldn't matter what these
        # are set to; the wizard should stop after the first step.
        irrelevant = (
            'us_sanctioned_country',
            'us_national_or_permanent_resident',
            'living_in_us',
        )

        for reject_field, reject_value in reject_if:
            for other_field in irrelevant:
                fields = {
                    reject_field: reject_value,
                    other_field: True,
                }
                with self.subTest(fields=fields):
                    self.assertEligible(
                        ApprovalStatus.REJECTED,
                        'GENERAL',
                        self.approved_work_eligibility(**fields),
                        self.barriers_to_participation(),
                        self.promotional(),
                    )

    def test_gathering_us_demographics(self):
        for condition, data in self.not_usa_demographics():
            with self.subTest(condition=condition):
                self.assertEligible(
                    ApprovalStatus.PENDING,
                    'ESSAY',
                    self.gender_identity('man'),
                    *data,
                )

    def test_approve_all_gender_identities(self):
        """
        Verify that, for each gender in the gender identity list, an
        applicant with that gender is put in the pending state
        (meaning they aren't automatically rejected).
        Also check that whether they're a US citizen or
        resident has no effect if the US rules aren't met.
        """
        for condition, data in self.not_usa_demographics():
            for gender_identity in self.all_gender_identities:
                genders = [gender_identity]
                with self.subTest(condition=condition, genders=genders):
                    self.assertEligible(
                        ApprovalStatus.PENDING,
                        'ESSAY',
                        self.gender_identity(*genders),
                        self.time_commitments(),
                        *data,
                    )

    def make_formset(self, forms):
        answers = {
            f"{idx}-{k}": v
            for idx, form in enumerate(forms)
            for k, v in form.items()
        }
        answers["TOTAL_FORMS"] = str(len(forms))
        answers["INITIAL_FORMS"] = "0"
        return answers

    def assertTimeEligible(self, expected_status, expected_reason, school=None, coding_school=None, employed=False, contractor=False, employment=None, time=None):
        kinds = []
        data = [
            self.approved_work_eligibility(),
            self.approved_payment_eligibility(),
            self.approved_foss_experience(),
            self.gender_identity(self.all_gender_identities[0]),
            self.barriers_to_participation(),
            self.promotional(),
        ]
        if school:
            kinds.append('enrolled_as_student')
            data.append(('School Info', {
                "university_name": "Example U",
                "university_website": "https://example.edu/",
                "current_academic_calendar": "https://example.edu/cal1",
                "next_academic_calendar": "https://example.edu/cal2",
                "degree_name": "Geology",
            }))
            data.append(('School Term Info', self.make_formset(school)))
        if coding_school:
            kinds.append('enrolled_as_noncollege_student')
            data.append(('Coding School or Online Courses Time Commitment Info', self.make_formset(coding_school)))
        if employed or (contractor and contractor["continuing_contract_work"]):
            data.append(('Employment Info', self.make_formset(employment)))
        if employed:
            kinds.append('employed')
        if contractor:
            kinds.append('contractor')
            data.append(('Contractor Info', self.make_formset([contractor])))
        if time:
            kinds.append('volunteer_time_commitments')
            data.append(('Volunteer Time Commitment Info', self.make_formset(time)))

        data.append(self.time_commitments(*kinds))

        self.assertEligible(expected_status, expected_reason, *data)

    def vacation(self, days):
        before = {
            'start_date': self.application_round.internstarts,
            'end_date': self.application_round.internstarts + timedelta(days=5),
            "term_name": "before",
        }
        after = {
            'start_date': self.application_round.internstarts + timedelta(days=5+days+1),
            'end_date': self.application_round.internends,
            "term_name": "after",
            "last_term": "True",
        }
        return [before, after]

    def test_approve_job_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            employed=True,
            employment=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 20,
                'job_title': 'Fancy Pants',
                'job_description': 'I wear the pants',
                'quit_on_acceptance': False,
            }],
        )

    def test_reject_job_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            employed=True,
            employment=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 21,
                'job_title': 'Overworked Fancy Pants',
                'job_description': 'I wear the pants',
                'quit_on_acceptance': False,
            }],
        )

    def test_approve_contractor_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            contractor={
                'continuing_contract_work': True,
                'typical_hours': 20,
            },
            employment=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 20,
                'job_title': 'Overworked Fancy Pants',
                'job_description': 'I wear the pants',
                'quit_on_acceptance': False,
            }],
        )

    def test_approve_contractor_commitment_if_quit(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            contractor={
                'continuing_contract_work': False,
                'typical_hours': 40,
            },
        )

    def test_reject_contractor_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            contractor={
                'continuing_contract_work': True,
                'typical_hours': 21,
            },
            employment=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 21,
                'job_title': 'Overworked Fancy Pants',
                'job_description': 'I wear the pants',
                'quit_on_acceptance': False,
            }],
        )

    def test_approve_time_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            time=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 20,
            }],
        )

    def test_reject_time_commitment(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            time=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 21,
            }],
        )

    def test_reject_full_time_school(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            school=[{
                'term_name': "term",
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                "last_term": "True",
            }],
        )

    def test_approve_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            school=self.vacation(days=42),
        )

    def test_reject_short_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            school=self.vacation(days=41),
        )

    def test_reject_full_time_coding_school(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            coding_school=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 21,
                'description': 'In-person coding school.',
                'quit_on_acceptance': False,
            }],
        )

    def test_accept_quitting_full_time_coding_school(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            coding_school=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 21,
                'description': 'Self-paced online coding school.',
                'quit_on_acceptance': True,
            }],
        )

    def test_accept_part_time_coding_school(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            coding_school=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'hours_per_week': 20,
                'description': 'Self-paced online coding school.',
                'quit_on_acceptance': False,
            }],
        )
