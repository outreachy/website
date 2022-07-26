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
class CommunityDocsTestCase(TestCase):
    def test_sponsorship_increase_visible(self):
        """
        This tests that an increase in sponsor amounts per intern is displayed correctly in the community docs
        """
        last_cohort = factories.RoundPageFactory(start_from='feedback3_due', sponsorship_per_intern=5000)
        
        response = self.client.get(reverse('docs-community'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p>All communities must find finding for at least one intern ($5,000 USD):</p>', html=True)
        self.assertContains(response, '<p><b>Other communities</b> must secure their own funding for at least one intern ($5,000 USD). After that external funding is secured, they can apply for additional interns to be funded by the Outreachy general fund.</p>', html=True)
        self.assertContains(response, '<p>The sponsorship for each Outreachy intern is $5,000 USD.</p>', html=True)

        # Create a second internship cohort with a different sponsorship amount per intern
        current_cohort = factories.RoundPageFactory(start_from='pingnew', days_after_today=-1, sponsorship_per_intern=10000)

        response = self.client.get(reverse('docs-community'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p>All communities must find finding for at least one intern ($10,000 USD):</p>', html=True)
        self.assertContains(response, '<p><b>Other communities</b> must secure their own funding for at least one intern ($10,000 USD). After that external funding is secured, they can apply for additional interns to be funded by the Outreachy general fund.</p>', html=True)
        self.assertContains(response, '<p>The sponsorship for each Outreachy intern is $10,000 USD.</p>', html=True)

