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
            ("not logged in", None),
            ("no comrade", factories.UserFactory()),
            ("only comrade", factories.ComradeFactory().account),
            ("applicant", scenario.applicant1.applicant.account),
            ("mentor", scenario.mentor.account),
            ("coordinator", scenario.coordinator.account),
            ("reviewer", scenario.reviewer.account),
        )

    def test_access_denied(self):
        """
        This tests that sponsor information is not visible to anyone who isn't staff.
         - Create a community with one sponsor, who is approved to participate in the current round
         - Check that the sponsor page is not accessible
        """
        scenario = scenarios.InternSelectionScenario(
                sponsorship__amount=19500,
                sponsorship__name="Sponsor A",
                participation__approval_status=models.ApprovalStatus.APPROVED,
                )
        visitors = self.get_visitors(scenario)
        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(reverse('sponsor-info', kwargs={'round_slug': scenario.round.slug}))
                self.assertEqual(response.status_code, 302)
                if visitor_type == "not logged in":
                    self.assertEqual(response.url, '/login/?next=/{}/sponsor-info/'.format(scenario.round.slug))
                else:
                    self.assertEqual(response.url, '/django-admin/login/?next=/{}/sponsor-info/'.format(scenario.round.slug))

    def test_sponsor_info_visible(self):
        """
        This tests that sponsor information is visible to staff.
         - Create a community with one sponsor, who is approved to participate in the current round
         - Create a second community with two sponsors, who is approved to participate
         - Check that the sponsor page is visible
        """
        current_round = factories.RoundPageFactory(start_from='pingnew')
        
        # Create a community with one sponsor, who is approved to participate in the current round
        sponsorship_a = factories.SponsorshipFactory(
                participation__participating_round=current_round,
                participation__approval_status=models.ApprovalStatus.APPROVED,
                name="Sponsor A",
                amount=13000,
                funding_secured=True,
                )

        # Create a second community with one sponsor, who is approved to participate
        sponsorship_b = factories.SponsorshipFactory(
                participation__participating_round=current_round,
                participation__approval_status=models.ApprovalStatus.APPROVED,
                name="Sponsor B",
                amount=6500,
                funding_secured=True,
                )

        # Add a second sponsor to the second community
        sponsorship_c = factories.SponsorshipFactory(
                participation=sponsorship_b.participation,
                name="Sponsor C",
                amount=19500,
                funding_secured=True,
                )

        organizer = factories.ComradeFactory()
        organizer.account.is_staff = True
        organizer.account.save()

        self.client.logout()
        self.client.force_login(organizer.account)

        response = self.client.get(reverse('sponsor-info', kwargs={'round_slug': current_round.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td>Sponsor A</td>', html=True)
        self.assertContains(response, '<td>Sponsor B</td>', html=True)
        self.assertContains(response, '<td>Sponsor C</td>', html=True)
        self.assertContains(response, '<h3>{}</h3>'.format(sponsorship_a.participation.community.name), html=True)
        self.assertContains(response, '<h3>{}</h3>'.format(sponsorship_b.participation.community.name), html=True)
