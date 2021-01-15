from datetime import datetime, timedelta, timezone
from django.test import TestCase, override_settings
from django.urls import reverse
import unittest

from . import models
from .factories import MentorApprovalFactory
from .factories import ParticipationFactory
from .factories import ProjectFactory


# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RoundPageTestCase(TestCase):
    def test_round_closed_no_new_round(self):
        # Make a round where the internship start date was a month ago
        # Make an approved project in an approved community that is under that round
        project_title = "AAAAAAAAHHHHHHH! This is a bug!!"
        community_name = "AAAAAAAAHHHHHHH! This is a community name!!"
        past_project = ProjectFactory(
                approval_status=models.ApprovalStatus.APPROVED,
                project_round__approval_status=models.ApprovalStatus.APPROVED,
                project_round__community__name=community_name,
                short_title=project_title,
                project_round__participating_round__start_from='internstarts',
                project_round__participating_round__days_after_today=-30)

        # Grab the current project selection page
        response = self.client.get(reverse('project-selection'))
        # Page should return a normal status code of 200
        # Make sure that the contents don't include the approved project title from last round
        self.assertNotContains(response, project_title, status_code=200)

        # Grab the community and project CFP page
        response = self.client.get(reverse('community-cfp'))
        # Make sure that the contents don't include the community as currently participating
        self.assertNotContains(response, 'review the list of participating communities below who are looking for help', status_code=200)
        # Make sure the page shows the community as a past approved community
        self.assertContains(response, community_name, status_code=200)

    # def test_previous_community_signup(self):
        # Create a previous round with pingnew set to six months ago
        # Create a current round with pingnew set today
        # Create a community that participated in the previous round
        # Login as that community's approved coordinator
        # Go to /communities/cfp/ and ensure that community's name has a valid link on the page as a previous community
        # Follow that link - it should be /communities/cfp/community-slug/
        # On /communities/cfp/community-slug/ there should be two buttons 'Community will participate' and 'Community will not participate'
        # (one is to submit, one is to withdraw)
        # Click 'Community will participate' - round-page-slug/communities/community-slug/submit/
        # Fill out one sponsor
        # Should be redirected back to the community read-only page /communities/cfp/community-slug/
        # That page should have a button in it that says 'Pending Participation'
        # An email should have been sent to the Outreachy organizers
        # Log in as staff
        # Staff dashboard should show a pending action to approve the participation of the community
        # Approve the community's participation - round-slug/communities/community-slug/approve/
        # An email should have been sent to the community coordinators
        # Test to ensure both staff and approved coordinator can see the community landing page - round-slug/communities/community-slug/
        #
        # Test project creation and approval
        # Log out from coordinator role - should not be logged in at all
        # Go to /communities/cfp/ - a link to the community read-only page should be there
        #  - should be under the "Mentor for a Participating FOSS community" heading
        # Go to /communities/cfp/community-slug/
        # There should be a 'Submit a Project Proposal' button that links to round-slug/communities/community-slug/submit-project/
        # Create a Comrade for a mentor, login as them
        # 
        # Test co-mentor signup
        #
        # Subtest: Can a new community sign up? Can the coordinator see community A who was approved above
        # Create a new Comrade

    def test_mentor_sees_hidden_projects(self):
        # Before the Outreachy application period opens,
        # We allow mentors with an approved project in an approved community
        # to see all other approved projects (even if it's not in their community).
        participation = ParticipationFactory(
            approval_status=models.ApprovalStatus.APPROVED,
            participating_round__start_from='initial_applications_open',
            participating_round__days_after_today=10,
        )

        # Mentors with pending projects should only see their own project.
        pending_project_title = "AAAAAAAAHHHHHHH! This project is pending!!"
        pending_mentor_approval = MentorApprovalFactory(
            approval_status=models.ApprovalStatus.APPROVED,
            project__approval_status=models.ApprovalStatus.PENDING,
            project__short_title=pending_project_title,
            project__project_round=participation,
        )

        # Make a different mentor with an approved project under the same community
        approved_project_title = "AAAAAAAAHHHHHHH! This project is approved!!"
        approved_mentor_approval = MentorApprovalFactory(
            approval_status=models.ApprovalStatus.APPROVED,
            project__approval_status=models.ApprovalStatus.APPROVED,
            project__short_title=approved_project_title,
            project__project_round=participation,
        )

        # Login as the pending mentor
        self.client.force_login(pending_mentor_approval.mentor.account)

        response = self.client.get(reverse('project-selection'))
        # Make sure that the contents does include the mentor's pending project title
        self.assertContains(response, '<h2>Your Pending Outreachy Internship Projects</h2>', status_code=200)
        self.assertContains(response, pending_project_title, status_code=200)
        # Make sure that the contents does not include the other mentor's approved project title
        self.assertNotContains(response, approved_project_title, status_code=200)

        # Login as the approved mentor
        self.client.force_login(approved_mentor_approval.mentor.account)

        response = self.client.get(reverse('project-selection'))
        # Make sure that the contents does include the mentor's approved project title
        self.assertContains(response, approved_project_title, status_code=200)
        # Make sure that the contents does not include the other mentor's pending project title
        self.assertNotContains(response, pending_project_title, status_code=200)

        # TODO:
        # Set the pending project to approved and make sure both mentors can see both projects
        # Make a mentor who is approved under a different community
        # Make sure that mentor can see all three projects
        # Make sure all three mentors can see all projects on all community landing pages

    def test_application_round_open(self):
        # Make a round where the application period is open
        # Make an approved project in an approved community
        project_title = "AAAAAAAAHHHHHHH! The code works!!"
        community_name = "AAAAAAAAHHHHHHH! This is a community name!!"
        past_project = ProjectFactory(
                approval_status=models.ApprovalStatus.APPROVED,
                project_round__approval_status=models.ApprovalStatus.APPROVED,
                project_round__community__name=community_name,
                short_title=project_title,
                project_round__participating_round__start_from='initial_applications_open',
                project_round__participating_round__days_after_today=-10)

        # Grab the current project selection page
        response = self.client.get(reverse('project-selection'))
        # Page should return a normal status code of 200
        # Make sure that the contents does include the approved project title from this round
        self.assertContains(response, project_title, status_code=200)
        # Since the project has an on-time deadline it should still be open
        self.assertContains(response, '<h2 id="open-projects">Outreachy Open Projects</h2>', status_code=200)

        # Grab the community and project CFP page
        response = self.client.get(reverse('community-cfp'))
        # Make sure it includes the community as currently participating
        self.assertContains(response, 'Outreachy is seeking experienced open source contributors to act as mentors for Outreachy interns', status_code=200)
        # Make sure the page shows the community
        self.assertContains(response, community_name, status_code=200)
