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
