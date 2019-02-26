import datetime
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from . import models
from .factories import RoundPageFactory
from .factories import InternSelectionFactory
from .factories import InitialMentorFeedbackFactory
from .factories import MidpointMentorFeedbackFactory
from .factories import FinalMentorFeedbackFactory


# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InternSelectionTestCase(TestCase):
    def test_mentor_can_resign(self):
        for mentors_count in (1, 2):
            with self.subTest(mentors_count=mentors_count):
                internselection = InternSelectionFactory(
                    active=True,
                    mentors=mentors_count,
                )
                mentors = list(internselection.mentors.all())
                mentor = mentors.pop()

                path = reverse('resign-as-mentor', kwargs={
                    'round_slug': internselection.round().slug,
                    'community_slug': internselection.project.project_round.community.slug,
                    'project_slug': internselection.project.slug,
                    'applicant_username': internselection.applicant.applicant.account.username,
                })

                self.client.force_login(mentor.mentor.account)
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                self.assertQuerysetEqual(internselection.mentors.all(), mentors, transform=lambda x: x)

    @staticmethod
    def _mentor_feedback_form(internselection, **kwargs):
        defaults = {
            'in_contact': True,
            'asking_questions': True,
            'active_in_public': True,
            'provided_onboarding': True,
            'checkin_frequency': models.InitialMentorFeedback.ONCE_WEEKLY,
            'last_contact': internselection.initial_feedback_opens,
            'intern_response_time': models.InitialMentorFeedback.HOURS_12,
            'mentor_response_time': models.InitialMentorFeedback.HOURS_12,
            'payment_approved': True,
            'full_time_effort': True,
            'progress_report': 'Everything is fine.',
            'mentors_report': 'My intern is awesome',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
            'termination_reason': '',
        }
        defaults.update(kwargs)
        return defaults

    def _submit_mentor_feedback_form(self, internselection, stage, answers):
        mentor = internselection.mentors.get()
        self.client.force_login(mentor.mentor.account)

        path = reverse(stage + '-mentor-feedback', kwargs={
            'username': internselection.applicant.applicant.account.username,
        })

        return self.client.post(path, {
            # This is a dictionary comprehension that converts model-level
            # values to form/POST values. It assumes all form widgets accept
            # the str() representation of their type when the form is POSTed.
            # Values which are supposed to be unspecified can be provided as
            # None, in which case we don't POST that key at all.
            key: str(value)
            for key, value in answers.items()
            if value is not None
        })

    def test_mentor_can_give_initial_feedback(self):
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round__start_from='initialfeedback',
                )

                extension_date = None
                if request_extension:
                    extension_date = internselection.round().initialfeedback + datetime.timedelta(weeks=5)

                answers = self._mentor_feedback_form(internselection,
                    request_extension=request_extension,
                    extension_date=extension_date,
                )
                response = self._submit_mentor_feedback_form(internselection, 'initial', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.initialmentorfeedback

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_invalid_duplicate_mentor_feedback(self):
        today = datetime.date.today()
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            { 'allow_edits': False, 'intern_selection__initial_feedback_opens': today - week },
            { 'allow_edits': True, 'intern_selection__initial_feedback_opens': today + week },
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = InitialMentorFeedbackFactory(**params)
                internselection = prior.intern_selection

                answers = self._mentor_feedback_form(internselection)
                response = self._submit_mentor_feedback_form(internselection, 'initial', answers)

                # permission denied
                self.assertEqual(response.status_code, 403)

    def test_mentor_can_resubmit_feedback(self):
        prior = InitialMentorFeedbackFactory(allow_edits=True)
        internselection = prior.intern_selection

        answers = self._mentor_feedback_form(internselection)
        response = self._submit_mentor_feedback_form(internselection, 'initial', answers)
        self.assertEqual(response.status_code, 302)

        # discard all cached objects and reload from database
        internselection = models.InternSelection.objects.get(pk=internselection.pk)

        # will raise DoesNotExist if the view destroyed this feedback
        feedback = internselection.initialmentorfeedback

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        # we didn't create a version for the factory-generated object, so the
        # only version should be the one that the view records
        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_invalid_mentor_extension_request(self):
        round = RoundPageFactory(start_from='initialfeedback')

        range_error = "Extension date must be between {} and {}".format(
            round.initialfeedback,
            round.initialfeedback + datetime.timedelta(weeks=5),
        )
        extension_deltas = (
            (None, "If you're requesting an extension, this field is required."),
            (datetime.timedelta(days=-1), range_error),
            (datetime.timedelta(weeks=5, days=1), range_error),
        )
        for extension_delta, expected_error in extension_deltas:
            with self.subTest(extension_delta=extension_delta):
                internselection = InternSelectionFactory(
                    active=True,
                    round=round,
                )

                extension_date = None
                if extension_delta:
                    extension_date = round.initialfeedback + extension_delta

                answers = self._mentor_feedback_form(internselection,
                    request_extension=True,
                    extension_date=extension_date,
                )
                response = self._submit_mentor_feedback_form(internselection, 'initial', answers)
                self.assertEqual(response.status_code, 200)

                # view should not have created a feedback object
                with self.assertRaises(models.InitialMentorFeedback.DoesNotExist):
                    internselection.initialmentorfeedback

                self.assertFormError(response, "form", "extension_date", expected_error)

    @staticmethod
    def _intern_feedback_form(internselection, **kwargs):
        defaults = {
            'in_contact': True,
            'asking_questions': True,
            'active_in_public': True,
            'provided_onboarding': True,
            'checkin_frequency': models.InitialInternFeedback.ONCE_WEEKLY,
            'last_contact': internselection.initial_feedback_opens,
            'intern_response_time': models.InitialInternFeedback.HOURS_12,
            'mentor_response_time': models.InitialInternFeedback.HOURS_12,
            'mentor_support': 'My mentor is awesome.',
            'hours_worked': models.InitialInternFeedback.HOURS_40,
            'progress_report': 'Everything is fine.',
        }
        defaults.update(kwargs)
        return defaults

    def _submit_intern_feedback_form(self, internselection, stage, answers):
        self.client.force_login(internselection.applicant.applicant.account)

        return self.client.post(reverse(stage + '-intern-feedback'), {
            # This is a dictionary comprehension that converts model-level
            # values to form/POST values. It assumes all form widgets accept
            # the str() representation of their type when the form is POSTed.
            # Values which are supposed to be unspecified can be provided as
            # None, in which case we don't POST that key at all.
            key: str(value)
            for key, value in answers.items()
            if value is not None
        })

    def test_intern_can_give_initial_feedback(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='initialfeedback',
        )

        answers = self._intern_feedback_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'initial', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.initialinternfeedback

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _midpoint_mentor_feedback_form(internselection, **kwargs):
        defaults = {
            'intern_help_requests_frequency': models.MidpointMentorFeedback.MULTIPLE_WEEKLY,
            'mentor_help_response_time': models.MidpointMentorFeedback.HOURS_6,
            'intern_contribution_frequency': models.MidpointMentorFeedback.ONCE_WEEKLY,
            'mentor_review_response_time': models.MidpointMentorFeedback.HOURS_3,
            'intern_contribution_revision_time': models.MidpointMentorFeedback.DAYS_2,
            'last_contact': internselection.midpoint_feedback_opens,
            'payment_approved': True,
            'full_time_effort': True,
            'progress_report': 'Everything is fine.',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
            'termination_reason': '',
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_midpoint_feedback(self):
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round__start_from='midfeedback',
                )

                extension_date = None
                if request_extension:
                    extension_date = internselection.round().midfeedback + datetime.timedelta(weeks=5)

                answers = self._midpoint_mentor_feedback_form(internselection,
                    request_extension=request_extension,
                    extension_date=extension_date,
                )
                response = self._submit_mentor_feedback_form(internselection, 'midpoint', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.midpointmentorfeedback

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_invalid_duplicate_midpoint_mentor_feedback(self):
        today = datetime.date.today()
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            { 'allow_edits': False, 'intern_selection__midpoint_feedback_opens': today - week },
            { 'allow_edits': True, 'intern_selection__midpoint_feedback_opens': today + week },
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = MidpointMentorFeedbackFactory(**params)
                internselection = prior.intern_selection

                answers = self._midpoint_mentor_feedback_form(internselection)
                response = self._submit_mentor_feedback_form(internselection, 'midpoint', answers)

                # permission denied
                self.assertEqual(response.status_code, 403)

    @staticmethod
    def _midpoint_intern_feedback_form(internselection, **kwargs):
        defaults = {
            'intern_help_requests_frequency': models.MidpointInternFeedback.MULTIPLE_WEEKLY,
            'mentor_help_response_time': models.MidpointInternFeedback.HOURS_6,
            'intern_contribution_frequency': models.MidpointInternFeedback.ONCE_WEEKLY,
            'mentor_review_response_time': models.MidpointInternFeedback.HOURS_3,
            'intern_contribution_revision_time': models.MidpointInternFeedback.DAYS_2,
            'last_contact': internselection.initial_feedback_opens,
            'mentor_support': 'My mentor is awesome.',
            'hours_worked': models.InitialInternFeedback.HOURS_40,
            'progress_report': 'Everything is fine.',
        }
        defaults.update(kwargs)
        return defaults

    def test_intern_can_give_midpoint_feedback(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='midfeedback',
        )

        answers = self._midpoint_intern_feedback_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'midpoint', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.midpointinternfeedback

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _final_intern_feedback_form(internselection, **kwargs):
        defaults = {
            'intern_help_requests_frequency': models.FinalInternFeedback.MULTIPLE_WEEKLY,
            'mentor_help_response_time': models.FinalInternFeedback.HOURS_6,
            'intern_contribution_frequency': models.FinalInternFeedback.ONCE_WEEKLY,
            'mentor_review_response_time': models.FinalInternFeedback.HOURS_3,
            'intern_contribution_revision_time': models.FinalInternFeedback.DAYS_2,
            'last_contact': internselection.final_feedback_opens,
            'mentor_support': 'My mentor is awesome.',
            'hours_worked': models.FinalInternFeedback.HOURS_40,
            'progress_report': 'Everything is fine.',
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def _final_mentor_feedback_form(internselection, **kwargs):
        defaults = {
            'intern_help_requests_frequency': models.FinalMentorFeedback.MULTIPLE_WEEKLY,
            'mentor_help_response_time': models.FinalMentorFeedback.HOURS_6,
            'intern_contribution_frequency': models.FinalMentorFeedback.ONCE_WEEKLY,
            'mentor_review_response_time': models.FinalMentorFeedback.HOURS_3,
            'intern_contribution_revision_time': models.FinalMentorFeedback.DAYS_2,
            'last_contact': internselection.final_feedback_opens,
            'payment_approved': True,
            'full_time_effort': True,
            'progress_report': 'Everything is fine.',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
            'termination_reason': '',
            'mentoring_recommended': models.FinalMentorFeedback.NO_OPINION,
            'blog_frequency': models.FinalMentorFeedback.NO_OPINION,
            'blog_prompts_caused_writing': models.FinalMentorFeedback.NO_OPINION,
            'blog_prompts_caused_overhead': models.FinalMentorFeedback.NO_OPINION,
            'recommend_blog_prompts': models.FinalMentorFeedback.NO_OPINION,
            'zulip_caused_intern_discussion': models.FinalMentorFeedback.NO_OPINION,
            'zulip_caused_mentor_discussion': models.FinalMentorFeedback.NO_OPINION,
            'recommend_zulip': models.FinalMentorFeedback.NO_OPINION,
            'feedback_for_organizers': 'There are things you could improve but they are minor',
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_final_feedback(self):
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round__start_from='midfeedback',
                )

                extension_date = None
                if request_extension:
                    extension_date = internselection.round().midfeedback + datetime.timedelta(weeks=5)

                answers = self._final_mentor_feedback_form(internselection,
                    request_extension=request_extension,
                    extension_date=extension_date,
                )
                response = self._submit_mentor_feedback_form(internselection, 'final', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.finalmentorfeedback

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

