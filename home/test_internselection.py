import datetime
from django.test import Client, TestCase
from django.urls import reverse

from . import models
from .factories import InternSelectionFactory


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

    def test_mentor_can_give_initial_feedback(self):
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round__start_from='initialfeedback',
                )
                mentor = internselection.mentors.get()

                path = reverse('initial-mentor-feedback', kwargs={
                    'username': internselection.applicant.applicant.account.username,
                })

                extension_date = None
                if request_extension:
                    extension_date = internselection.round().initialfeedback + datetime.timedelta(weeks=5)

                answers = {
                    'in_contact': True,
                    'asking_questions': True,
                    'active_in_public': True,
                    'provided_onboarding': True,
                    'checkin_frequency': models.InitialMentorFeedback.ONCE_WEEKLY,
                    'last_contact': internselection.initial_feedback_opens,
                    'intern_response_time': models.InitialMentorFeedback.HOURS_12,
                    'mentor_response_time': models.InitialMentorFeedback.HOURS_12,
                    'progress_report': 'Everything is fine.',
                    'full_time_effort': True,
                    'request_extension': request_extension,
                    'extension_date': extension_date,
                }

                self.client.force_login(mentor.mentor.account)
                response = self.client.post(path, {
                    k: str(v)
                    for k, v in answers.items()
                    if v is not None
                })
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.initialmentorfeedback

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)
