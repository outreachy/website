import datetime
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from . import models
from .factories import *
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InternSelectionTestCase(TestCase):
    def test_intern_selection_process(self):
        for phase in ('contributions_open', 'contributions_close'):
            with self.subTest(phase=phase):
                current_round = RoundPageFactory(start_from=phase)
                applicantapproval = ApplicantApprovalFactory(
                    application_round=current_round,
                    approval_status=models.ApprovalStatus.APPROVED,
                )

                project = ProjectFactory(
                    project_round__participating_round=current_round,
                    approval_status=models.ApprovalStatus.APPROVED,
                    project_round__approval_status=models.ApprovalStatus.APPROVED,
                )

                finalapplication = FinalApplicationFactory(
                    round=current_round, project=project, applicant=applicantapproval
                )

                mentorapproval = MentorApprovalFactory(
                    project=project, approval_status=models.ApprovalStatus.APPROVED
                )

                coordinatorapproval = CoordinatorApprovalFactory(
                    community=project.project_round.community,
                    approval_status=models.ApprovalStatus.APPROVED,
                )

                organizer = ComradeFactory(account__is_staff=True).account

                post_params = {
                    "round_slug": current_round.slug,
                    "community_slug": project.project_round.community.slug,
                    "project_slug": project.slug,
                    "applicant_username": applicantapproval.applicant.account.username,
                }

                # mentor selects the intern..
                self.client.force_login(mentorapproval.mentor.account)
                path = reverse("select-intern", kwargs={**post_params})

                legal_name = mentorapproval.mentor.public_name
                response = self.client.post(path, {
                    "rating-rating": models.FinalApplication.AMAZING,
                    "contract-legal_name": legal_name,
                })
                self.assertEqual(response.status_code, 302)

                new_relationship = models.MentorRelationship.objects.get(mentor=mentorapproval)
                intern_selection = new_relationship.intern_selection
                self.assertEqual(new_relationship.contract.legal_name, legal_name)
                self.assertEqual(intern_selection.applicant, applicantapproval)
                self.assertEqual(intern_selection.project, project)

                # organizer approves too early, rejected..
                self.client.force_login(organizer)
                path = reverse("intern-approval", kwargs={
                    **post_params,
                    "approval": "Approved",
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 403)
                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.organizer_approved, None)

                # coordinator adds funding..
                self.client.force_login(coordinatorapproval.coordinator.account)
                path = reverse("intern-fund", kwargs={
                    **post_params,
                    "funding": models.InternSelection.GENERAL_FUNDED,
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.funding_source, models.InternSelection.GENERAL_FUNDED)

                # organizer approves..
                self.client.force_login(organizer)
                path = reverse("intern-approval", kwargs={
                    **post_params,
                    "approval": "Approved",
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.organizer_approved, True)

    def test_intern_selection_emails(self):
        scenario = scenarios.ContributionsClosedScenario()

        rejected_mentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.REJECTED
        )
        withdrawn_mentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.WITHDRAWN
        )
        approved_comentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.APPROVED
        )

        post_params = {
            "round_slug": scenario.round.slug,
            "community_slug": scenario.project.project_round.community.slug,
            "project_slug": scenario.project.slug,
            "applicant_username": scenario.applicant1.applicant.account.username,
        }
        legal_name = scenario.mentor.public_name

        # mentor selects the intern.
        self.client.force_login(scenario.mentor.account)
        path = reverse("select-intern", kwargs={**post_params})
        response = self.client.post(path, {
            "rating-rating": models.FinalApplication.AMAZING,
            "contract-legal_name": legal_name,
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Outreachy intern selected - please sign mentoring agreement')
        self.assertEqual(mail.outbox[0].from_email, organizers)

        # Check important links are in the email body
        comentor_sign_up_link = reverse('select-intern', kwargs={
            'round_slug': scenario.round.slug,
            'community_slug': scenario.community.slug,
            'project_slug' : scenario.project.slug,
            'applicant_username': scenario.applicant1.applicant.account.username,
        })
        project_applicants_link = reverse('project-applicants', kwargs={
            'round_slug': scenario.round.slug,
            'community_slug': scenario.community.slug,
            'project_slug' : scenario.project.slug,
        })
        self.assertIn(comentor_sign_up_link, mail.outbox[0].body)
        self.assertIn(project_applicants_link, mail.outbox[0].body)
        self.assertIn(reverse('alums'), mail.outbox[0].body)

        # The rejected and withdrawn mentors
        # should not get an email about the intern selection,
        # but the approved co-mentor should get an email.
        self.assertEqual(mail.outbox[0].to, [approved_comentor.mentor.email_address()])

    def test_mentor_can_resign(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        for mentors_count in (1, 2):
            with self.subTest(mentors_count=mentors_count):
                internselection = InternSelectionFactory(
                    active=True,
                    mentors=mentors_count,
                    round=current_round,
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
            'mentors_report': 'I am very supportive',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
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
        current_round = RoundPageFactory(start_from='initialfeedback')
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
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
        current_round = RoundPageFactory(start_from='initialfeedback')
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            {'allow_edits': False, 'intern_selection__initial_feedback_opens': current_round.initialfeedback - week},
            {'allow_edits': True, 'intern_selection__initial_feedback_opens': current_round.initialfeedback + week},
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = InitialMentorFeedbackFactory(intern_selection__round=current_round, **params)
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
            'time_comments': '',
            'progress_report': 'Everything is fine.',
            'share_mentor_feedback_with_community_coordinator': True,
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
            'mentors_report': 'I am very supportive',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_midpoint_feedback(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
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
        # The dates of the round don't matter because the views check the dates in the InternSelection
        current_round = RoundPageFactory(start_from='midfeedback')
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            {'allow_edits': False, 'intern_selection__midpoint_feedback_opens': current_round.midfeedback - week},
            {'allow_edits': True, 'intern_selection__midpoint_feedback_opens': current_round.midfeedback + week},
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = MidpointMentorFeedbackFactory(intern_selection__round=current_round, **params)
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
            'time_comments': '',
            'progress_report': 'Everything is fine.',
            'share_mentor_feedback_with_community_coordinator': True,
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
            'time_comments': '',
            'progress_report': 'Everything is fine.',
            'share_mentor_feedback_with_community_coordinator': True,
            'interning_recommended': models.FinalInternFeedback.YES,
            'recommend_intern_chat': models.FinalInternFeedback.NO_OPINION,
            'chat_frequency': models.FinalInternFeedback.WEEK2,
            'blog_frequency': models.FinalInternFeedback.WEEK3,
            'blog_prompts_caused_writing': models.FinalInternFeedback.YES,
            'blog_prompts_caused_overhead': models.FinalInternFeedback.YES,
            'recommend_blog_prompts': models.FinalInternFeedback.YES,
            'zulip_caused_intern_discussion': models.FinalInternFeedback.YES,
            'zulip_caused_mentor_discussion': models.FinalInternFeedback.NO,
            'recommend_zulip': models.FinalInternFeedback.YES,
            'tech_industry_prep': models.FinalInternFeedback.NO,
            'foss_confidence': models.FinalInternFeedback.YES,
            'feedback_for_organizers': 'This was a really awesome internship!',
        }
        defaults.update(kwargs)
        return defaults

    def test_intern_can_give_final_feedback(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='finalfeedback',
        )

        answers = self._final_intern_feedback_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'final', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.finalinternfeedback

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

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
            'mentors_report': 'I am very supportive',
            'request_extension': False,
            'extension_date': None,
            'request_termination': False,
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
        current_round = RoundPageFactory(start_from='finalfeedback')
        for request_extension in (False, True):
            with self.subTest(request_extension=request_extension):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
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

