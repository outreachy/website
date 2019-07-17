import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.formats import date_format

from home import models
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProjectSubmissionTestCase(TestCase):

    def test_initial_application_marked_closed(self):
        """
        This tests how the website works before we start accepting initial applications
         - Create a new RoundPage for the upcoming round where initial_applications_open has not passed
         - /apply/eligibility/ should not have a button to submit an application
         - it should not have a prompt to submit an application
         - it should have a prompt saying initial applications are currently closed
        """
        current_round = factories.RoundPageFactory(start_from='initial_applications_open', days_after_today=1)

        response = self.client.get(reverse('eligibility-information'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p>The application system for Outreachy internships is currently closed. The application system will be available when the application period opens on {} at 4pm UTC. Initial applications are due on {} 4pm UTC.</p>'.format(date_format(current_round.initial_applications_open), date_format(current_round.initial_applications_close)), html=True)
