import datetime
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from . import models
from .factories import *

class ProjectSubmissionTestCase(TestCase):
    def test_community_cfp_closed(self):
        # This is before we have a new RoundPage for the upcoming round,
        # and after the interns are announced for the last round.
        # InternshipWeekScenario(week=5)
        #
        # /community/cfp should be linked from the mentor instructions (currently in the Wagtail CRM)
        # /community/cfp should be linked from the navigational menu
        # - Volunteers -> 'Add a community'
        # - Volunteers -> 'Submit a project'
        # - Volunteers -> 'Co-mentor a project'
        #
        # On /community/cfp:
        #  - The generic timeline should be visible.
        #  - There should not be a button to submit a new community to participate.
        #  - Communities who have participated in the past should be listed on the website.
        #  - There should be a list of communities who were not approved to participate in any round.
        #  - Historic communities (with no participation objects at all) should be listed separately.
        #
        # New community coordinators should be able to sign up for the upcoming round:
        #  - Click on a community from /community/cfp/
        #  - The page should have a warning box about community sign up being closed
        #    "Project and community CFP is currently closed"
        #  - There should be a link to the coordinator duties "/mentor/#coordinator"
        #  - There should be a button "Coordinate for this Community"
        #  - CoordinatorApproval submission form should work
        #  - Outreachy organizers and current approved Coordinators should get an email notification
        #  - following the link sent from that email should allow both approval and rejection
        #  - the person should get an email on both approval or rejection
        #  - the rejection email should include the reason for rejection
        #  - approval should now show the coordinator listed on the community read-only page
        #
        # Sign up to be notified when the community is participating in the next round:
        #  - Click on a community from /community/cfp/
        #  - There should be a "Notify me" button
        #  - Notification form should work
        #  - When the round opens, everyone who signed up to be notified should get an email
        pass

    def test_community_cfp_open(self):
        # This is when we have a new RoundPage and the community sign-ups are open
        # today = datetime.date.today()
        # NewRoundScenario(round__start_from='pingnew', round__start_date=today)
        #
        # On /community/cfp:
        #  - The timeline for this round should now be visible.
        #  - The "Community sign up opens" should match today's date
        #  - Past participating communities should include the one created by NewRoundScenario
        #  - Create a "historic" community - it should be shown
        #  - Create an "unapproved" community from last round - should be shown
        #
        # Past coordinator signing up for the current round:
        #  - Go to /community/cfp/
        #  - Follow the link for your community
        #  - Get confused by why there's a 'sign-up to coordinate' button when you're a coordinator
        #  - Log into the website, which should redirect back to the community read-only page
        #  - There should be a success color 'Community Will Participate' button
        #  - Click that button, fill out funding form
        #  - The community read-only page should now reflect that the community has signed up
        #    - Coordinator actions box with 'Update community info' button
        #    - Community status box should read 'Pending Participation'
        #    - Funding should reflect funding levels coordinator put in
        #    - 'No projects' are approved by the coordinator yet
        #    - 'Open to new projects' - mentors can submit projects
        #    - 'Submit a Project Proposal' button for mentors to submit projects
        #    - A link to the mentor FAQ should be visible 'mentor requirements'
        #  - Outreachy organizers should get an email about the community sign up
        #
        # Mentor should be able to submit a project:
        #  - FIXME - need detailed description of this process
        #
        # Organizer approving the community:
        #  - Outreachy organizers should follow the link from the email, log in, and be able to approve the community
        #  - The link should have an 'Approve Community' button
        #  - Need to click a second approve button on the double confirmation page
        #  - Redirect back to community read-only page
        #  - Coordinator receives email that the community was approved to participate
        #  - The community read-only page should now reflect that the community has been approved
        #    - Community status box should read 'Participating'
        #
        # Organizer approving the community:
        #  - Outreachy organizers should follow the link from the email, log in, and be able to reject the community
        #  - The link should have an warning color 'Reject Community' button
        #  - Need to click a second reject button on the double confirmation page, and provide a reason for rejection
        #  - Redirect back to community read-only page
        #  - Coordinator will not receive automated email that they were rejected - organizers will send a personalized email
        #  - The community read-only page should now reflect that the community has not been approved
        #    - Community status box should read 'Not Participating'
        #  - The community should not show up under /apply/project-selection/
        #  - Any approved projects for that community should not show up on /apply/project-selection/
        #
        # Past coordinator saying the community will not participate:
        #  - Go to /community/cfp/
        #  - Follow the link for your community
        #  - Get confused by why there's a 'sign-up to coordinate' button when you're a coordinator
        #  - Log into the website, which should redirect back to the community read-only page
        #  - There should be a warning color 'Community Will Not Participate' button
        pass
