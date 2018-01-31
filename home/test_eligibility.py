from datetime import date, timedelta
from django.test import SimpleTestCase

from .models import ApprovalStatus, RoundPage
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

    eligible_genders = (
        'transgender',
        'genderqueer',
        'woman',
        'demi_boy',
        'demi_girl',
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
    )

    checked_genders = (
        ('prefer_not_to_say', True),
        ('self_identify', 'some other thing not already listed'),
    )

    @staticmethod
    def approved_general_info(**kwargs):
        defaults = {
            # these must be answered this way to get approved:
            'over_18': True,
            'gsoc_or_outreachy_internship': False,
            'eligible_to_work': True,
            'under_export_control': False,
            'us_sanctioned_country': False,
            # these questions only affect later questions:
            'us_national_or_permanent_resident': False,
            'living_in_us': False,
        }
        defaults.update(kwargs)
        return ('General Info', defaults)

    @staticmethod
    def usa_demographics(us_resident_demographics):
        return ('USA demographics', {'us_resident_demographics': us_resident_demographics})

    @classmethod
    def not_usa_demographics(cls):
        """
        Returns an iterator over situations where an applicant can't be
        deemed automatically eligible under the US rules, so they need
        to be evaluated under other rules instead.
        """
        yield ('non-US', (
            cls.approved_general_info(),
        ))

        us_conditions = ('us_national_or_permanent_resident', 'living_in_us')
        for condition in us_conditions:
            yield (condition, (
                cls.approved_general_info(**{condition: True}),
                cls.usa_demographics(False),
            ))

    @classmethod
    def gender_identity(cls, *args, **kwargs):
        defaults = {
            gender: False
            for gender in ('man', 'prefer_not_to_say') + cls.eligible_genders
        }
        defaults['self_identify'] = ''
        for arg in args:
            defaults[arg] = True
        defaults.update(kwargs)
        return ('Gender Identity', defaults)

    @staticmethod
    def time_commitments(*args):
        defaults = {
            'enrolled_as_student': False,
            'employed': False,
            'contractor': False,
            'time_commitments': False,
        }
        for arg in args:
            defaults[arg] = True
        return ('Time Commitments', defaults)

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
            ('gsoc_or_outreachy_internship', True),
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
                        'DEMOGRAPHICS',
                        self.approved_general_info(**fields),
                    )

    def test_reject_gender(self):
        for condition, data in self.not_usa_demographics():
            with self.subTest(condition=condition):
                self.assertEligible(
                    ApprovalStatus.REJECTED,
                    'DEMOGRAPHICS',
                    self.gender_identity('man'),
                    *data,
                )

    def test_approve_gender(self):
        """
        Verify that, for each gender in the eligible genders list, an
        applicant with that gender either alone or in addition to 'man'
        is approved. Also check that whether they're a US citizen or
        resident has no effect if the US rules aren't met.
        """
        for condition, data in self.not_usa_demographics():
            for others in ([], ['man']):
                for eligible in self.eligible_genders:
                    genders = others + [eligible]
                    with self.subTest(condition=condition, genders=genders):
                        self.assertEligible(
                            ApprovalStatus.APPROVED,
                            '',
                            self.gender_identity(*genders),
                            self.time_commitments(),
                            *data,
                        )

    def test_pending_gender(self):
        """
        Verify that, for each gender in the checked genders list, an
        applicant with that gender gets marked pending, no matter what
        other genders (if any) are selected too. Also check that whether
        they're a US citizen or resident has no effect if the US rules
        aren't met.
        """
        for condition, data in self.not_usa_demographics():
            for others in [[], ['man']] + [[eligible] for eligible in self.eligible_genders]:
                for gender, value in self.checked_genders:
                    genders = others + [gender]
                    with self.subTest(condition=condition, genders=genders):
                        self.assertEligible(
                            ApprovalStatus.PENDING,
                            '',
                            self.approved_general_info(),
                            self.gender_identity(*others, **{gender: value}),
                            self.time_commitments(),
                        )

    def test_approved_us_demographics(self):
        """
        A US applicant should be approved if they meet the US-specific
        eligibility conditions, no matter what they report for gender.
        """
        us_conditions = ('us_national_or_permanent_resident', 'living_in_us')
        for condition in us_conditions:
            for gender in ('man', 'prefer_not_to_say', self.eligible_genders[0]):
                with self.subTest(gender=gender, condition=condition):
                    self.assertEligible(
                        ApprovalStatus.APPROVED,
                        '',
                        self.approved_general_info(**{condition: True}),
                        self.usa_demographics(True),
                        self.gender_identity(gender),
                        self.time_commitments(),
                    )

    def assertTimeEligible(self, expected_status, expected_reason, school=None, contractor=False, employment=None, time=None):
        kinds = []
        data = [
            self.approved_general_info(),
            self.gender_identity(self.eligible_genders[0]),
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
            kinds.append('time_commitments')
            data.append(('Time Commitment Info', list(time) + [None]))

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
            ApprovalStatus.APPROVED,
            '',
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

    def test_approve_half_time_school(self):
        self.assertTimeEligible(
            ApprovalStatus.APPROVED,
            '',
            school=[{
                'start_date': self.application_round.internstarts,
                'end_date': self.application_round.internends,
                'registered_credits': 6,
                'outreachy_credits': 0,
                'thesis_credits': 0,
                'typical_credits': 12,
            }],
        )

    def test_approve_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.APPROVED,
            '',
            school=self.vacation(days=49,
                registered_credits=12,
                outreachy_credits=0,
                thesis_credits=0,
                typical_credits=12,
            ),
        )

    def test_reject_short_school_vacation(self):
        self.assertTimeEligible(
            ApprovalStatus.REJECTED,
            'TIME',
            school=self.vacation(days=48,
                registered_credits=12,
                outreachy_credits=0,
                thesis_credits=0,
                typical_credits=12,
            ),
        )
