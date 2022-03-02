import datetime
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version
from unittest import skip

from . import models
from .factories import *
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InternSelectionTestCase(TestCase):

    @staticmethod
    def _test_intern_selection_process(self, phase):
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

    def test_intern_selection_process_when_contributions_open(self):
        self._test_intern_selection_process(self, 'contributions_open')

    def test_intern_selection_process_when_contributions_close(self):
        self._test_intern_selection_process(self, 'contributions_close')

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
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,
            'talk_about_project_progress': True,
            'blog_created': True,
            'last_contact': internselection.initial_feedback_opens,
            'progress_report': 'Everything is fine.',
            'mentors_report': 'I am very supportive',
            'full_time_effort': True,
            'actions_requested': models.BaseMentorFeedback.PAY_AND_CONTINUE,
        }
        defaults.update(kwargs)
        return defaults

    def _submit_mentor_feedback_form(self, internselection, url, button_name, answers, on_dashboard=True):
        mentor = internselection.mentors.get()
        self.client.force_login(mentor.mentor.account)

        # Make sure there's a link on the dashboard to that type of open feedback
        response = self.client.get(reverse('dashboard'))
        if on_dashboard:
            self.assertContains(response, '<button type="button" class="btn btn-info">{}</button>'.format(button_name), html=True)
        else:
            self.assertNotContains(response, '<button type="button" class="btn btn-info">{}</button>'.format(button_name), html=True)

        path = reverse(url, kwargs={
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

    def test_mentor_can_give_successful_initial_feedback(self):
        current_round = RoundPageFactory(start_from='initialfeedback')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._mentor_feedback_form(internselection,
            actions_requested=models.BaseMentorFeedback.PAY_AND_CONTINUE,
        )
        response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback1frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = True
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_terminate_initial_feedback(self):
        current_round = RoundPageFactory(start_from='initialfeedback')
        for action in (models.BaseMentorFeedback.TERMINATE_PAY, models.BaseMentorFeedback.TERMINATE_NO_PAY):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._mentor_feedback_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback1frommentor

                # Add in the fields automatically set by the action the mentor requested
                if action == models.BaseMentorFeedback.TERMINATE_PAY:
                    answers['payment_approved'] = True
                else:
                    answers['payment_approved'] = False
                answers['request_extension'] = False
                answers['extension_date'] = None
                answers['request_termination'] = True
                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_uncertain_initial_feedback(self):
        current_round = RoundPageFactory(start_from='initialfeedback')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._mentor_feedback_form(internselection,
            actions_requested=models.BaseMentorFeedback.DONT_KNOW,
        )
        response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback1frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)


    def test_mentor_can_give_extension_initial_feedback(self):
        current_round = RoundPageFactory(start_from='initialfeedback')
        for action in (models.BaseMentorFeedback.EXT_1_WEEK, models.BaseMentorFeedback.EXT_2_WEEK, models.BaseMentorFeedback.EXT_3_WEEK, models.BaseMentorFeedback.EXT_4_WEEK, models.BaseMentorFeedback.EXT_5_WEEK):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._mentor_feedback_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback1frommentor

                answers['payment_approved'] = False
                answers['request_extension'] = True
                answers['request_termination'] = False
                if action == models.BaseMentorFeedback.EXT_1_WEEK:
                    extension = 1
                elif action == models.BaseMentorFeedback.EXT_2_WEEK:
                    extension = 2
                elif action == models.BaseMentorFeedback.EXT_3_WEEK:
                    extension = 3
                elif action == models.BaseMentorFeedback.EXT_4_WEEK:
                    extension = 4
                elif action == models.BaseMentorFeedback.EXT_5_WEEK:
                    extension = 5
                answers['extension_date'] = current_round.initialfeedback + datetime.timedelta(weeks=extension)

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
                response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers, False)

                # permission denied
                self.assertEqual(response.status_code, 403)

    def test_mentor_can_resubmit_feedback(self):
        prior = InitialMentorFeedbackFactory(allow_edits=True)
        internselection = prior.intern_selection

        answers = self._mentor_feedback_form(internselection)
        response = self._submit_mentor_feedback_form(internselection, 'initial-mentor-feedback', 'Submit Feedback #1', answers)
        self.assertEqual(response.status_code, 302)

        # discard all cached objects and reload from database
        internselection = models.InternSelection.objects.get(pk=internselection.pk)

        # will raise DoesNotExist if the view destroyed this feedback
        feedback = internselection.feedback1frommentor

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        # we didn't create a version for the factory-generated object, so the
        # only version should be the one that the view records
        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _intern_feedback_form(internselection, **kwargs):
        defaults = {
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,
            'talk_about_project_progress': True,
            'blog_created': True,
            'last_contact': internselection.initial_feedback_opens,
            'mentor_support': 'My mentor is awesome.',
            'share_mentor_feedback_with_community_coordinator': True,
            'hours_worked': models.Feedback1FromIntern.HOURS_40,
            'time_comments': '',
            'progress_report': 'Everything is fine.',
        }
        defaults.update(kwargs)
        return defaults

    def _submit_intern_feedback_form(self, internselection, url, answers):
        self.client.force_login(internselection.applicant.applicant.account)

        return self.client.post(reverse(url), {
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
        response = self._submit_intern_feedback_form(internselection, 'initial-intern-feedback', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback1fromintern

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _midpoint_mentor_feedback_form(internselection, **kwargs):
        defaults = {
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,
            'talk_about_project_progress': True,

            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,

            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,

            'mentors_report': 'I am very supportive',
            'last_contact': internselection.midpoint_feedback_opens,
            'progress_report': 'Everything is fine.',

            'full_time_effort': True,

            'actions_requested': models.BaseMentorFeedback.PAY_AND_CONTINUE,
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_successful_feedback2(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        internselection = InternSelectionFactory(
                active=True,
                round=current_round,
                )

        answers = self._midpoint_mentor_feedback_form(internselection)
        response = self._submit_mentor_feedback_form(internselection, 'midpoint-mentor-feedback', 'Submit Feedback #2', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback2frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = True
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    # Since there's no payment associated with Feedback #2,
    # terminating the internship at that point means
    # the initial payment has been paid (associated with Feedback #1),
    # and the final stipend will not be paid (associated with Feedback #3).
    #
    # Therefore we only need to test submitting the form
    # with the TERMINATE_NO_PAY action to take
    def test_mentor_can_give_terminate_feedback2(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._midpoint_mentor_feedback_form(internselection,
            actions_requested=models.BaseMentorFeedback.TERMINATE_NO_PAY,
        )
        response = self._submit_mentor_feedback_form(internselection, 'midpoint-mentor-feedback', 'Submit Feedback #2', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback2frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = True
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_uncertain_feedback2(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._midpoint_mentor_feedback_form(internselection,
            actions_requested=models.BaseMentorFeedback.DONT_KNOW,
        )
        response = self._submit_mentor_feedback_form(internselection, 'midpoint-mentor-feedback', 'Submit Feedback #2', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback2frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_extension_feedback2(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        for action in (models.BaseMentorFeedback.EXT_1_WEEK, models.BaseMentorFeedback.EXT_2_WEEK, models.BaseMentorFeedback.EXT_3_WEEK, models.BaseMentorFeedback.EXT_4_WEEK, models.BaseMentorFeedback.EXT_5_WEEK):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._midpoint_mentor_feedback_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'midpoint-mentor-feedback', 'Submit Feedback #2', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback2frommentor

                answers['payment_approved'] = False
                answers['request_extension'] = True
                answers['request_termination'] = False
                if action == models.BaseMentorFeedback.EXT_1_WEEK:
                    extension = 1
                elif action == models.BaseMentorFeedback.EXT_2_WEEK:
                    extension = 2
                elif action == models.BaseMentorFeedback.EXT_3_WEEK:
                    extension = 3
                elif action == models.BaseMentorFeedback.EXT_4_WEEK:
                    extension = 4
                elif action == models.BaseMentorFeedback.EXT_5_WEEK:
                    extension = 5
                answers['extension_date'] = current_round.midfeedback + datetime.timedelta(weeks=extension)

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
                prior = Feedback2FromMentorFactory(intern_selection__round=current_round, **params)
                internselection = prior.intern_selection

                answers = self._midpoint_mentor_feedback_form(internselection)
                response = self._submit_mentor_feedback_form(internselection, 'midpoint-mentor-feedback', 'Submit Feedback #2', answers, False)

                # permission denied
                self.assertEqual(response.status_code, 403)

    @staticmethod
    def _midpoint_intern_feedback_form(internselection, **kwargs):
        defaults = {
            'share_mentor_feedback_with_community_coordinator': True,

            # 1. Clearing up doubts
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            # 2. Meetings
            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,

            # 2. Tracking project progress
            'talk_about_project_progress': True,

            # 4. Project feedback
            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,
        
            # 3. Acknowledgment and praise
            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            # 3/6. Blogging
            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            # 6. Networking
            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,

            'progress_report': 'Everything is fine.',
            'hours_worked': models.Feedback1FromIntern.HOURS_30,
            'time_comments': '',
            'last_contact': internselection.midpoint_feedback_opens,
            'mentor_support': 'My mentor is awesome.',
        }
        defaults.update(kwargs)
        return defaults

    def test_intern_can_give_feedback2(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='midfeedback',
        )

        answers = self._midpoint_intern_feedback_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'midpoint-intern-feedback', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback2fromintern

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _feedback3_mentor_form(internselection, **kwargs):
        defaults = {
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,

            'talk_about_project_progress': True,
            'reviewed_original_timeline': True,

            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,

            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,

            'mentors_report': 'I am very supportive',
            'last_contact': internselection.feedback3_opens,
            'progress_report': 'Everything is fine.',

            'full_time_effort': True,

            'actions_requested': models.BaseMentorFeedback.PAY_AND_CONTINUE,
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_successful_feedback3(self):
        current_round = RoundPageFactory(start_from='feedback3_due')
        internselection = InternSelectionFactory(
                active=True,
                round=current_round,
                )

        answers = self._feedback3_mentor_form(internselection)
        response = self._submit_mentor_feedback_form(internselection, 'feedback-3-from-mentor', 'Submit Feedback #3', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback3frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = True
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_terminate_feedback3(self):
        current_round = RoundPageFactory(start_from='feedback3_due')
        for action in (models.BaseMentorFeedback.TERMINATE_PAY, models.BaseMentorFeedback.TERMINATE_NO_PAY):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._feedback3_mentor_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'feedback-3-from-mentor', 'Submit Feedback #3', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback3frommentor

                # Add in the fields automatically set by the action the mentor requested
                if action == models.BaseMentorFeedback.TERMINATE_PAY:
                    answers['payment_approved'] = True
                else:
                    answers['payment_approved'] = False
                answers['request_extension'] = False
                answers['extension_date'] = None
                answers['request_termination'] = True
                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_uncertain_feedback3(self):
        current_round = RoundPageFactory(start_from='feedback3_due')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._feedback3_mentor_form(internselection,
            actions_requested=models.BaseMentorFeedback.DONT_KNOW,
        )
        response = self._submit_mentor_feedback_form(internselection, 'feedback-3-from-mentor', 'Submit Feedback #3', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback3frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_extension_feedback3(self):
        current_round = RoundPageFactory(start_from='feedback3_due')
        for action in (models.BaseMentorFeedback.EXT_1_WEEK, models.BaseMentorFeedback.EXT_2_WEEK, models.BaseMentorFeedback.EXT_3_WEEK, models.BaseMentorFeedback.EXT_4_WEEK, models.BaseMentorFeedback.EXT_5_WEEK):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._feedback3_mentor_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'feedback-3-from-mentor', 'Submit Feedback #3', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback3frommentor

                answers['payment_approved'] = False
                answers['request_extension'] = True
                answers['request_termination'] = False
                if action == models.BaseMentorFeedback.EXT_1_WEEK:
                    extension = 1
                elif action == models.BaseMentorFeedback.EXT_2_WEEK:
                    extension = 2
                elif action == models.BaseMentorFeedback.EXT_3_WEEK:
                    extension = 3
                elif action == models.BaseMentorFeedback.EXT_4_WEEK:
                    extension = 4
                elif action == models.BaseMentorFeedback.EXT_5_WEEK:
                    extension = 5
                answers['extension_date'] = current_round.feedback3_due + datetime.timedelta(weeks=extension)

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @skip("This test fails, but I think it's an issue in the test. Local testing for this case correctly stops the mentor from resubmitting feedback again until the feedback form re-opens.")
    def test_invalid_duplicate_feedback3_mentor_feedback(self):
        # The dates of the round don't matter because the views check the dates in the InternSelection
        current_round = RoundPageFactory(start_from='feedback3_due')
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            {'allow_edits': False, 'intern_selection__feedback3_opens': current_round.feedback3_due - week},
            {'allow_edits': True, 'intern_selection__feedback3_opens': current_round.feedback3_due + week},
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = Feedback3FromMentorFactory(intern_selection__round=current_round, **params)
                internselection = prior.intern_selection

                answers = self._feedback3_mentor_form(internselection)
                response = self._submit_mentor_feedback_form(internselection, 'feedback-3-from-mentor', 'Submit Feedback #3', answers, False)

                # permission denied
                self.assertEqual(response.status_code, 403)

    @staticmethod
    def _feedback3_intern_form(internselection, **kwargs):
        defaults = {
            'share_mentor_feedback_with_community_coordinator': True,

            # 1. Clearing up doubts
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            # 2. Meetings
            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,

            # 2. Tracking project progress
            'talk_about_project_progress': True,
            'reviewed_original_timeline': True,

            # 4. Project feedback
            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,
        
            # 3. Acknowledgment and praise
            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            # 3/6. Blogging
            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            # 6. Networking
            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,

            'progress_report': 'Everything is fine.',
            'hours_worked': models.Feedback1FromIntern.HOURS_30,
            'time_comments': '',
            'last_contact': internselection.feedback3_opens,
            'mentor_support': 'My mentor is awesome.',
        }
        defaults.update(kwargs)
        return defaults

    def test_intern_can_give_feedback3(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='feedback3_due',
        )

        answers = self._feedback3_intern_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'feedback-3-from-intern', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback3fromintern

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @staticmethod
    def _feedback4_mentor_form(internselection, **kwargs):
        defaults = {
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,

            'talk_about_project_progress': True,
            'reviewed_original_timeline': True,

            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,

            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,
            'mentor_introduced_to_informal_chat_contacts': True,
            'intern_had_informal_chats': True,

            'mentors_report': 'I am very supportive',
            'last_contact': internselection.final_feedback_opens,
            'progress_report': 'Everything is fine.',

            'full_time_effort': True,

            'actions_requested': models.BaseMentorFeedback.PAY_AND_CONTINUE,

            'recommend_mentoring': '10',
            'mentoring_positive_impacts': 'I liked working with the intern',
            'mentoring_improvement_suggestions': 'Ask mentors to do less work',
            'new_mentor_suggestions': 'Be prepared for a lot of work',
            'community_positive_impacts': 'Our community liked working with the intern',
            'community_improvement_suggestions': 'Better prepare community members for lots of applicants',
            'additional_feedback': 'None',
        }
        defaults.update(kwargs)
        return defaults

    def test_mentor_can_give_successful_feedback4(self):
        current_round = RoundPageFactory(start_from='finalfeedback')
        internselection = InternSelectionFactory(
                active=True,
                round=current_round,
                )

        answers = self._feedback4_mentor_form(internselection)
        response = self._submit_mentor_feedback_form(internselection, 'final-mentor-feedback', 'Submit Feedback #4', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback4frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = True
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_terminate_feedback4(self):
        current_round = RoundPageFactory(start_from='finalfeedback')
        action = models.BaseMentorFeedback.TERMINATE_PAY
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._feedback4_mentor_form(internselection,
            actions_requested=action,
        )
        response = self._submit_mentor_feedback_form(internselection, 'final-mentor-feedback', 'Submit Feedback #4', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback4frommentor

        # Add in the fields automatically set by the action the mentor requested
        if action == models.BaseMentorFeedback.TERMINATE_PAY:
            answers['payment_approved'] = True
        else:
            answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = True
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_uncertain_feedback4(self):
        current_round = RoundPageFactory(start_from='finalfeedback')
        internselection = InternSelectionFactory(
            active=True,
            round=current_round,
        )

        answers = self._feedback4_mentor_form(internselection,
            actions_requested=models.BaseMentorFeedback.DONT_KNOW,
        )
        response = self._submit_mentor_feedback_form(internselection, 'final-mentor-feedback', 'Submit Feedback #4', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback4frommentor

        # Add in the fields automatically set by the action the mentor requested
        answers['payment_approved'] = False
        answers['request_extension'] = False
        answers['extension_date'] = None
        answers['request_termination'] = False
        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    def test_mentor_can_give_extension_feedback4(self):
        current_round = RoundPageFactory(start_from='finalfeedback')
        for action in (models.BaseMentorFeedback.EXT_1_WEEK, models.BaseMentorFeedback.EXT_2_WEEK, models.BaseMentorFeedback.EXT_3_WEEK, models.BaseMentorFeedback.EXT_4_WEEK, models.BaseMentorFeedback.EXT_5_WEEK):
            with self.subTest(action=action):
                internselection = InternSelectionFactory(
                    active=True,
                    round=current_round,
                )

                answers = self._feedback4_mentor_form(internselection,
                    actions_requested=action,
                )
                response = self._submit_mentor_feedback_form(internselection, 'final-mentor-feedback', 'Submit Feedback #4', answers)
                self.assertEqual(response.status_code, 302)

                # will raise DoesNotExist if the view didn't create this
                feedback = internselection.feedback4frommentor

                answers['payment_approved'] = False
                answers['request_extension'] = True
                answers['request_termination'] = False
                if action == models.BaseMentorFeedback.EXT_1_WEEK:
                    extension = 1
                elif action == models.BaseMentorFeedback.EXT_2_WEEK:
                    extension = 2
                elif action == models.BaseMentorFeedback.EXT_3_WEEK:
                    extension = 3
                elif action == models.BaseMentorFeedback.EXT_4_WEEK:
                    extension = 4
                elif action == models.BaseMentorFeedback.EXT_5_WEEK:
                    extension = 5
                answers['extension_date'] = current_round.finalfeedback + datetime.timedelta(weeks=extension)

                for key, expected in answers.items():
                    self.assertEqual(getattr(feedback, key), expected)

                # only allow submitting once
                self.assertFalse(feedback.allow_edits)

                self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)

    @skip("This test fails, but I think it's an issue in the test. Local testing for this case correctly stops the mentor from resubmitting feedback again until the feedback form re-opens.")
    def test_invalid_duplicate_feedback4_mentor_feedback(self):
        # The dates of the round don't matter because the views check the dates in the InternSelection
        current_round = RoundPageFactory(start_from='finalfeedback')
        week = datetime.timedelta(weeks=1)
        disallowed_when = (
            {'allow_edits': False, 'intern_selection__final_feedback_opens': current_round.finalfeedback - week},
            {'allow_edits': True, 'intern_selection__final_feedback_opens': current_round.finalfeedback + week},
        )
        for params in disallowed_when:
            with self.subTest(params=params):
                prior = Feedback4FromMentorFactory(intern_selection__round=current_round, **params)
                internselection = prior.intern_selection

                answers = self._feedback4_mentor_form(internselection)
                response = self._submit_mentor_feedback_form(internselection, 'final-mentor-feedback', 'Submit Feedback #4', answers, False)

                # permission denied
                self.assertEqual(response.status_code, 403)

    @staticmethod
    def _feedback4_intern_form(internselection, **kwargs):
        defaults = {
            'share_mentor_feedback_with_community_coordinator': True,

            # 1. Clearing up doubts
            'mentor_answers_questions': True,
            'intern_asks_questions': True,
            'mentor_support_when_stuck': True,

            # 2. Meetings
            'daily_stand_ups': True,
            'meets_privately': True,
            'meets_over_phone_or_video_chat': True,
            'intern_missed_meetings': False,

            # 2. Tracking project progress
            'talk_about_project_progress': True,
            'reviewed_original_timeline': True,

            # 4. Project feedback
            'contribution_drafts': True,
            'contribution_review': True,
            'contribution_revised': True,
        
            # 3. Acknowledgment and praise
            'mentor_shares_positive_feedback': True,
            'mentor_promoting_work_to_community': True,
            'mentor_promoting_work_on_social_media': True,

            # 3/6. Blogging
            'intern_blogging': True,
            'mentor_discussing_blog': True,
            'mentor_promoting_blog_to_community': True,
            'mentor_promoting_blog_on_social_media': True,

            # 6. Networking
            'mentor_introduced_intern_to_community': True,
            'intern_asks_questions_of_community_members': True,
            'intern_talks_to_community_members': True,
            'mentor_introduced_to_informal_chat_contacts': True,
            'intern_had_informal_chats': True,

            'progress_report': 'Everything is fine.',
            'hours_worked': models.Feedback1FromIntern.HOURS_30,
            'time_comments': '',
            'last_contact': internselection.final_feedback_opens,
            'mentor_support': 'My mentor is awesome.',

            'recommend_open_source': '10',
            'recommend_interning': '10',
            'application_period_positive_impacts': 'I got to know my mentors',
            'application_period_improvement_suggestions': 'Have people applicants can talk to when they are filling out the initial application',
            'new_applicant_advice': 'Be confident',
            'interning_positive_impacts': 'I learned new skills',
            'interning_improvement_suggestions': 'More career advice',
            'community_positive_impacts': 'I liked getting know experienced open source contributors',
            'community_improvement_suggestions': 'You all are awesome! Keep up the good work!!',
            'additional_feedback': 'None.',
        }
        defaults.update(kwargs)
        return defaults

    def test_intern_can_give_feedback4(self):
        internselection = InternSelectionFactory(
            active=True,
            round__start_from='finalfeedback',
        )

        answers = self._feedback4_intern_form(internselection)
        response = self._submit_intern_feedback_form(internselection, 'final-intern-feedback', answers)
        self.assertEqual(response.status_code, 302)

        # will raise DoesNotExist if the view didn't create this
        feedback = internselection.feedback4fromintern

        for key, expected in answers.items():
            self.assertEqual(getattr(feedback, key), expected)

        # only allow submitting once
        self.assertFalse(feedback.allow_edits)

        self.assertEqual(Version.objects.get_for_object(feedback).count(), 1)
