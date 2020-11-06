import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from home import models
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProjectSubmissionTestCase(TestCase):

    def get_visitors(self, scenario):
        return (
            ("only comrade", factories.ComradeFactory().account),
            ("applicant", scenario.applicant1.applicant.account),
            ("mentor", scenario.mentor.account),
            ("coordinator", scenario.coordinator.account),
        )

    def test_login_required(self):
        """
        This tests that the page to review interns requires users to be logged in.
        """
        scenario = scenarios.InternSelectionScenario(
                applicant1__applicant__public_name="Inez Intern",
                )

        self.client.logout()
        response = self.client.get(reverse('review-interns', kwargs={'round_slug': scenario.round.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/?next=/{}/review-interns/'.format(scenario.round.slug))

    def test_access_denied(self):
        """
        This tests that sponsor information is not visible to anyone who isn't staff.
         - Create a community with one sponsor, who is approved to participate in the current round
         - Check that the sponsor page is not accessible
        """
        scenario = scenarios.InternSelectionScenario(
                applicant1__applicant__public_name="Inez Intern",
                )
        visitors = self.get_visitors(scenario)
        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(reverse('review-interns', kwargs={'round_slug': scenario.round.slug}))
                self.assertEqual(response.status_code, 403)

    def test_visible_to_organizers(self):
        """
        This tests that intern review page is visible to anyone with staff privileges (Outreachy organizers).
        """
        scenario = scenarios.InternSelectionScenario(
                applicant1__applicant__public_name="Applicant 1",
                applicant2__applicant__public_name="Applicant 2",
                )

        organizer = factories.ComradeFactory()
        organizer.account.is_staff = True
        organizer.account.save()

        self.client.logout()
        self.client.force_login(organizer.account)

        response = self.client.get(reverse('review-interns', kwargs={'round_slug': scenario.round.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td><a href="#intern-{}">Applicant 1</a></td>'.format(scenario.applicant1.applicant.account.pk), html=True)
        self.assertContains(response, '<td><a href="#intern-{}">Applicant 2</a></td>'.format(scenario.applicant2.applicant.account.pk), html=True)

    def test_visible_to_applicant_reviewers(self):
        """
        This tests that intern review page is visible to approved applicant reviewers.
        """
        scenario = scenarios.InternSelectionScenario(
                applicant1__applicant__public_name="Applicant 1",
                applicant2__applicant__public_name="Applicant 2",
                )

        self.client.logout()
        self.client.force_login(scenario.reviewer.account)

        response = self.client.get(reverse('review-interns', kwargs={'round_slug': scenario.round.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td><a href="#intern-{}">Applicant 1</a></td>'.format(scenario.applicant1.applicant.account.pk), html=True)
        self.assertContains(response, '<td><a href="#intern-{}">Applicant 2</a></td>'.format(scenario.applicant2.applicant.account.pk), html=True)
