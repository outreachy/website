from datetime import datetime, timedelta, timezone, date
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from reversion.models import Version
import unittest

from . import models
from .factories import MentorApprovalFactory
from .factories import ProjectFactory


# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RoundPageTestCase(TestCase):
    def test_round_closed_no_new_round(self):
        # Make a round where the internship start date was a month ago
        # Make an approved project in an approved community that is under that round
        past = datetime.now(timezone.utc) - timedelta(days=30)
        project_title = "AAAAAAAAHHHHHHH! This is a bug!!"
        past_project = ProjectFactory(
                approval_status=models.ApprovalStatus.APPROVED,
                project_round__approval_status=models.ApprovalStatus.APPROVED,
                short_title=project_title,
                project_round__participating_round__start_from='internstarts',
                project_round__participating_round__start_date=past)

        # Grab the current project selection page
        response = self.client.post(reverse('project-selection'))
        # Page should return a normal status code of 200
        # Make sure that the contents don't include the approved project title from last round
        self.assertNotContains(response, project_title, status_code=200)

    def test_application_round_open(self):
        # Make a round where the application period is open
        # Make an approved project in an approved community
        open_date = datetime.now(timezone.utc) - timedelta(days=10)
        project_title = "AAAAAAAAHHHHHHH! The code works!!"
        past_project = ProjectFactory(
                approval_status=models.ApprovalStatus.APPROVED,
                project_round__approval_status=models.ApprovalStatus.APPROVED,
                short_title=project_title,
                project_round__participating_round__start_from='appsopen',
                project_round__participating_round__start_date=open_date)

        # Grab the current project selection page
        response = self.client.post(reverse('project-selection'))
        # Page should return a normal status code of 200
        # Make sure that the contents does include the approved project title from this round
        self.assertContains(response, project_title, status_code=200)
        # Since the project has an on-time deadline it should still be open
        self.assertContains(response, '<h2 id="open-projects">Outreachy Open Projects</h2>', status_code=200)
