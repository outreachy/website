import datetime
from django.test import TestCase, override_settings
from django.urls import reverse
from home import models
from home import factories
from home import scenarios

FEEDBACK_SUMMARY_URLS = [
    'initial-feedback-summary',
    'midpoint-feedback-summary',
    'feedback-3-summary',
    'final-feedback-summary',
]

def make_feedback1_from_intern(
    intern_selection, share_with_coordinator=False,
    mentor_support='Test mentor support',
    progress_report='Test intern progress report'
):
    return models.Feedback1FromIntern.objects.create(
        intern_selection=intern_selection,
        allow_edits=False,
        ip_address='127.0.0.1',
        last_contact=datetime.date.today(),
        hours_worked=models.BaseInternFeedback.HOURS_30,
        mentor_support=mentor_support,
        share_mentor_feedback_with_community_coordinator=share_with_coordinator,
        mentor_answers_questions=True,
        intern_asks_questions=True,
        mentor_support_when_stuck=True,
        meets_privately=True,
        meets_over_phone_or_video_chat=True,
        intern_missed_meetings=False,
        talk_about_project_progress=True,
        blog_created=True,
        progress_report=progress_report,
    )


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class FeedbackSummaryAccessTest(TestCase):
    """Tests access control for the four feedback summary views."""

    def setUp(self):
        self.scenario = scenarios.InternSelectionScenario(
            applicant1__applicant__public_name="Applicant 1",
            applicant2__applicant__public_name="Applicant 2",
        )
        self.round_slug = self.scenario.round.slug
        self.organizer = factories.ComradeFactory()
        self.organizer.account.is_staff = True
        self.organizer.account.save()

    def test_login_required(self):
        """Unauthenticated users are redirected to the login page."""
        self.client.logout()
        for url_name in FEEDBACK_SUMMARY_URLS:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, kwargs={'round_slug': self.round_slug}))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login/', response.url)

    def test_non_coordinator_non_staff_denied(self):
        """Logged-in users who are not staff or a coordinator for this round are denied."""
        visitors = [
            ('comrade', factories.ComradeFactory().account),
            ('applicant', self.scenario.applicant1.applicant.account),
            ('mentor', self.scenario.mentor.account),
        ]
        for url_name in FEEDBACK_SUMMARY_URLS:
            for visitor_type, account in visitors:
                with self.subTest(url=url_name, visitor=visitor_type):
                    self.client.force_login(account)
                    response = self.client.get(reverse(url_name, kwargs={'round_slug': self.round_slug}))
                    self.assertEqual(response.status_code, 403)

    def test_staff_can_access_all_feedback_summaries(self):
        """Outreachy organizers (staff) can access all four feedback summary pages."""
        self.client.force_login(self.organizer.account)
        for url_name in FEEDBACK_SUMMARY_URLS:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, kwargs={'round_slug': self.round_slug}))
                self.assertEqual(response.status_code, 200)

    def test_coordinator_can_access_all_feedback_summaries(self):
        """Community coordinators can access all four feedback summary pages."""
        self.client.force_login(self.scenario.coordinator.account)
        for url_name in FEEDBACK_SUMMARY_URLS:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, kwargs={'round_slug': self.round_slug}))
                self.assertEqual(response.status_code, 200)

    def test_coordinator_from_other_community_is_denied(self):
        """A coordinator who is not approved for any community in this round is denied."""
        other_coordinator = factories.CoordinatorFactory()
        self.client.force_login(other_coordinator.account)
        for url_name in FEEDBACK_SUMMARY_URLS:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, kwargs={'round_slug': self.round_slug}))
                self.assertEqual(response.status_code, 403)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class FeedbackSummaryCommunityFilterTest(TestCase):
    """Tests that coordinators only see interns from their own community."""

    def setUp(self):
        self.scenario = scenarios.InternSelectionScenario(
            applicant2__applicant__public_name="Community 1 Intern",
        )
        self.round_slug = self.scenario.round.slug

        # Create a second approved intern in a different community in the same round.
        # Pass round= as a Param so InternSelectionFactory reuses the existing round
        # rather than creating a new one (which would conflict on slug).
        self.other_intern = factories.InternSelectionFactory(
            round=self.scenario.round,
            organizer_approved=True,
            applicant__applicant__public_name="Community 2 Intern",
            project__project_round__approval_status=models.ApprovalStatus.APPROVED,
        )

        self.organizer = factories.ComradeFactory()
        self.organizer.account.is_staff = True
        self.organizer.account.save()

    def test_coordinator_sees_only_their_community_interns(self):
        """
        A coordinator for community 1 sees only community 1's interns,
        not interns from community 2 in the same round.
        """
        self.client.force_login(self.scenario.coordinator.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Community 1 Intern')
        self.assertNotContains(response, 'Community 2 Intern')

    def test_staff_sees_interns_from_all_communities(self):
        """Staff see interns from all communities in the round."""
        self.client.force_login(self.organizer.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Community 1 Intern')
        self.assertContains(response, 'Community 2 Intern')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class FeedbackSummaryContentTest(TestCase):
    """Tests what coordinators and staff can see in the feedback content."""

    def setUp(self):
        self.scenario = scenarios.InternSelectionScenario(
            applicant2__applicant__public_name="Test Intern",
        )
        self.round_slug = self.scenario.round.slug
        self.intern_selection = self.scenario.intern_selection2

        self.organizer = factories.ComradeFactory()
        self.organizer.account.is_staff = True
        self.organizer.account.save()

    def test_coordinator_sees_intern_progress_report(self):
        """Coordinators can see the intern's progress report."""
        make_feedback1_from_intern(
            self.intern_selection,
            progress_report='My project is progressing well.',
        )
        self.client.force_login(self.scenario.coordinator.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertContains(response, 'My project is progressing well.')

    def test_staff_sees_intern_progress_report(self):
        """Staff can see the intern's progress report."""
        make_feedback1_from_intern(
            self.intern_selection,
            progress_report='My project is progressing well.',
        )
        self.client.force_login(self.organizer.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertContains(response, 'My project is progressing well.')

    def test_coordinator_sees_mentor_support_when_intern_opted_in(self):
        """
        Coordinators see the intern's comments about their mentor
        when the intern opted to share them with the coordinator.
        """
        make_feedback1_from_intern(
            self.intern_selection,
            share_with_coordinator=True,
            mentor_support='My mentor responds quickly.',
        )
        self.client.force_login(self.scenario.coordinator.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertContains(response, 'My mentor responds quickly.')

    def test_coordinator_cannot_see_mentor_support_without_opt_in(self):
        """
        Coordinators cannot see the intern's comments about their mentor
        when the intern did not opt to share them with the coordinator.
        """
        make_feedback1_from_intern(
            self.intern_selection,
            share_with_coordinator=False,
            mentor_support='Private mentor feedback.',
        )
        self.client.force_login(self.scenario.coordinator.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertNotContains(response, 'Private mentor feedback.')

    def test_staff_sees_mentor_support_regardless_of_opt_in(self):
        """Staff can always see the intern's comments about their mentor."""
        make_feedback1_from_intern(
            self.intern_selection,
            share_with_coordinator=False,
            mentor_support='Staff-only mentor feedback.',
        )
        self.client.force_login(self.organizer.account)
        response = self.client.get(reverse('initial-feedback-summary', kwargs={'round_slug': self.round_slug}))
        self.assertContains(response, 'Staff-only mentor feedback.')
