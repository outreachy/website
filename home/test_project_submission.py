import datetime
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from home.models import *
from home.factories import *
from home.scenarios import *

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProjectSubmissionTestCase(TestCase):

    # The following tests apply to the community read-only page text
    # e.g. home/templates/home/community_read_only.html

    def get_visitors_from_past_round(self, scenario):
        return (
            ("not logged in", None),
            ("no comrade", factories.UserFactory()),
            ("only comrade", factories.ComradeFactory().account),
            ("organizer", factories.ComradeFactory(account__is_staff=True).account),
            ("applicant", scenario.applicant1.applicant.account),
            ("mentor", scenario.mentor.account),
            ("coordinator", scenario.coordinator.account),
            ("reviewer", scenario.reviewer.account),
        )

    def test_community_read_only_submission_text_cfp_closed(self):
        """
        This tests how the page for coordinators and mentors of a community
        looks between rounds (after interns have been selected
        but before the next round has been announced).

        Test home/templates/home/community_read_only.html:
         - Create a community that has been approved to participate in a past round
         - No new RoundPage for the upcoming round
         - Check:
           - Warning card about CFP not being open is visible
           - The 'Submit a Project Proposal' button is not visible
           - The 'Submit an Outreachy Intern Project Proposal' heading is not visible
         - Ensure those checks are true for all visitor types
        """
        scenario = InternshipWeekScenario(week = 1, community__name='Debian', community__slug='debian')
        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        project_submission_path = reverse('project-action', kwargs={'action': 'submit', 'round_slug': scenario.participation.participating_round.slug, 'community_slug': scenario.participation.community.slug, })

        visitors = self.get_visitors_from_past_round(scenario)

        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<div class="card-header text-white bg-warning">Project and community CFP is currently closed</div>', html=True)
                self.assertNotContains(response, '<h2>Submit an Outreachy Intern Project Proposal</h2>', html=True)
                self.assertNotContains(response, '<a class="btn btn-success" href="{}">Submit a Project Proposal</a>'.format(project_submission_path), html=True)

    def test_community_read_only_submission_text_cfp_open_uncertain_participation(self):
        """
        This tests how the page for coordinators and mentors of a community
        looks after a new round has been announced,
        but before the community signs up to participate.

        Test home/templates/home/community_read_only.html:
         - Create a community that has been approved to participate in a past round
         - Create a new RoundPage for the upcoming round
         - Check:
           - The 'Not Participating' status is visible
           - The 'Coordinate for This Community' button is visible to anyone who is not a coordinator
           - The 'Community will participate' button is visible to a coordinator
           - The 'Community will not participate' button is visible to a coordinator
           - The 'Submit a Project Proposal' button is not visible
           - The 'Submit an Outreachy Intern Project Proposal' heading is not visible
        """
        scenario = InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        current_round = RoundPageFactory(start_from='pingnew')

        project_submission_path = reverse('project-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        coordinator_signup_path = reverse('coordinatorapproval-action', kwargs={'action': 'submit', 'community_slug': scenario.participation.community.slug, })
        community_does_participate_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        community_does_not_participate_path = reverse('participation-action', kwargs={'action': 'withdraw', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })

        visitors = self.get_visitors_from_past_round(scenario)

        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<span class="badge badge-pill badge-warning">Not Participating</span>', html=True)
                if visitor_type != 'coordinator':
                    self.assertContains(response, '<a href="{}" class="btn btn-success">Coordinate for This Community</a>'.format(coordinator_signup_path), html=True)
                else:
                    self.assertContains(response, '<a href="{}" class="btn btn-success">Community will participate</a>'.format(community_does_participate_path), html=True)
                    self.assertContains(response, '<a href="{}" class="btn btn-warning">Community will not participate</a>'.format(community_does_not_participate_path), html=True)
                self.assertNotContains(response, '<h2>Submit an Outreachy Intern Project Proposal</h2>', html=True)
                self.assertNotContains(response, '<a class="btn btn-success" href="{}">Submit a Project Proposal</a>'.format(project_submission_path), html=True)

    def test_community_participation_signup_too_early(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
         - Create a new RoundPage for the upcoming round where the CFP hasn't opened
         - Try to submit the community to participate in the round through the form
         - It should fail
        """
        scenario = InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = RoundPageFactory(start_from='pingnew', start_date=datetime.date.today() + datetime.timedelta(days=1))

        community_does_participate_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        self.client.force_login(scenario.coordinator.account)
        sponsor_name = 'Software in the Public Interest - Debian'
        sponsor_amount = 13000
        response = self.client.post(community_does_participate_path, {
            'sponsorship_set-TOTAL_FORMS': '1',
            'sponsorship_set-INITIAL_FORMS': '0',
            'sponsorship_set-MIN_NUM_FORMS': '0',
            'sponsorship_set-MAX_NUM_FORMS': '1000',
            'sponsorship_set-0-name': sponsor_name,
            'sponsorship_set-0-amount': sponsor_amount,
            'sponsorship_set-0-funding_secured': 'on',
            'sponsorship_set-0-funding_decision_date': str(datetime.date.today()),
        })
        with self.assertRaises(Participation.DoesNotExist):
            p = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug)
        self.assertNotEqual(response.status_code, 302)
        pass

    def test_community_participation_signup(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
         - Create a new RoundPage for the upcoming round
         - Submit the community to participate in the round through the form
         - There should be an email sent to the Outreachy organizers about the participation
         - There should be a Participation object for this community in the current round marked as PENDING

        Test home/templates/home/community_read_only.html:
         - Check:
           - The 'Pending Participation' status is visible
           - Funding for 1 intern is visible
           - The 'Coordinate for This Community' button is visible to anyone who is not a coordinator
           - The 'Submit a Project Proposal' button is visible
           - The 'Submit an Outreachy Intern Project Proposal' heading is visible
           - The 'Community will participate' button is visible to a coordinator
           - The 'Community will not participate' button is visible to a coordinator
        """
        scenario = InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = RoundPageFactory(start_from='pingnew')

        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        project_submission_path = reverse('project-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        coordinator_signup_path = reverse('coordinatorapproval-action', kwargs={'action': 'submit', 'community_slug': scenario.participation.community.slug, })
        community_does_participate_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        community_does_not_participate_path = reverse('participation-action', kwargs={'action': 'withdraw', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })

        visitors = self.get_visitors_from_past_round(scenario)
        # There should not be a Participation for Debian in the current round yet
        with self.assertRaises(Participation.DoesNotExist):
            p = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug)

        self.client.force_login(scenario.coordinator.account)
        sponsor_name = 'Software in the Public Interest - Debian'
        sponsor_amount = 13000
        response = self.client.post(community_does_participate_path, {
            'sponsorship_set-TOTAL_FORMS': '1',
            'sponsorship_set-INITIAL_FORMS': '0',
            'sponsorship_set-MIN_NUM_FORMS': '0',
            'sponsorship_set-MAX_NUM_FORMS': '1000',
            'sponsorship_set-0-name': sponsor_name,
            'sponsorship_set-0-amount': sponsor_amount,
            'sponsorship_set-0-funding_secured': 'on',
            'sponsorship_set-0-funding_decision_date': str(datetime.date.today()),
        })
        self.assertEqual(response.status_code, 302)
        participation = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug, approval_status=ApprovalStatus.PENDING)
        sponsorship = Sponsorship.objects.get(participation=participation, coordinator_can_update=True, name=sponsor_name, amount=sponsor_amount, funding_secured=True)

        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<span class="badge badge-pill badge-info">Pending Participation</span>', html=True)
                if visitor_type != 'coordinator':
                    self.assertContains(response, '<a href="{}" class="btn btn-success">Coordinate for This Community</a>'.format(coordinator_signup_path), html=True)
                self.assertContains(response, '<h2>Submit an Outreachy Intern Project Proposal</h2>', html=True)
                self.assertContains(response, '<a class="btn btn-success" href="{}">Submit a Project Proposal</a>'.format(project_submission_path), html=True)

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
        #  - There should be a link to the coordinator duties "/mentor/#coordinator"
        #  x There should be a button "Coordinate for this Community"
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
