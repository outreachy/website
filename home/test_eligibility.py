from datetime import date, timedelta
from django.test import SimpleTestCase

from .models import ApprovalStatus, RoundPage, PromotionTracking
from .views import determine_eligibility, EligibilityUpdateView

class MockWizard(object):
    """
    Emulate enough of the interface of
    formtools.wizard.views.SessionWizardView to convince the eligibility
    checks that this is a real wizard instance.
    """

    def __init__(self, *data):
        self.data = dict(data)

    def get_cleaned_data_for_step(self, step):
        return self.data.get(step)

class EligibilityTests(SimpleTestCase):

    application_round = RoundPage(
        internstarts=date(2018, 3, 1),
        internends=date(2018, 6, 1),
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
            'lacking_representation': 'Yes',
            'systemic_bias': 'Yes',
            'employment_bias': 'Yes',
            'barriers_to_contribution': "I don't know",
        }
        defaults.update(kwargs)
        return ('Barriers to Participation', defaults)

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
        wizard = MockWizard(*data)

        for step, form in EligibilityUpdateView.form_list:
            condition = EligibilityUpdateView.condition_dict.get(step,
                    lambda wizard: True)
            if condition(wizard):
                self.assertIn(step, wizard.data.keys())
            else:
                self.assertNotIn(step, wizard.data.keys())

        status, reason = determine_eligibility(wizard, self.application_round)
        self.assertEqual(status, expected_status)
        self.assertEqual(reason, expected_reason)

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

    def assertTimeEligible(self, expected_status, expected_reason, school=None, contractor=False, employment=None, time=None):
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
            data.append(('School Info', [{}]))
            data.append(('School Term Info', list(school) + [None]))
        if employment:
            if contractor:
                kinds.append('contractor')
                data.append(('Contractor Info', [{'continuing_contract_work': True}]))
            else:
                kinds.append('employed')
            data.append(('Employment Info', list(employment) + [None]))
        if time:
            kinds.append('volunteer_time_commitments')
            data.append(('Volunteer Time Commitment Info', list(time) + [None]))

        data.append(self.time_commitments(*kinds))

        self.assertEligible(expected_status, expected_reason, *data)

    def vacation(self, days, **kwargs):
        before = {
            'start_date': self.application_round.internstarts,
            'end_date': self.application_round.internstarts + timedelta(days=5),
        }
        after = {
            'start_date': self.application_round.internstarts + timedelta(days=5+days+1),
            'end_date': self.application_round.internends,
        }
        before.update(kwargs)
        after.update(kwargs)
        return [before, after]

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
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
            }],
        )

    def test_approve_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.PENDING,
            'ESSAY',
            school=self.vacation(days=49),
        )

    def test_reject_short_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            school=self.vacation(days=48),
        )
