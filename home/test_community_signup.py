import datetime
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
import pprint
from reversion.models import Version

from home.models import *
from home import factories
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProjectSubmissionTestCase(TestCase):

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

    def check_community_signup_marked_closed(self):
        response = self.client.get(reverse('community-cfp'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<h2>Submit a New FOSS community for Organizer Review</h2>', html=True)
        self.assertNotContains(response, '<a class="btn btn-success" href="{}">Submit a New Community</a>'.format(reverse('community-add')), html=True)

    def coordinator_signs_up_community_to_participate(self, community_does_participate_path, sponsor_name='Software in the Public Interest - Debian', sponsor_amount=13000):
        return self.client.post(community_does_participate_path, {
            'sponsorship_set-TOTAL_FORMS': '1',
            'sponsorship_set-INITIAL_FORMS': '0',
            'sponsorship_set-MIN_NUM_FORMS': '0',
            'sponsorship_set-MAX_NUM_FORMS': '1000',
            'sponsorship_set-0-name': sponsor_name,
            'sponsorship_set-0-amount': sponsor_amount,
            'sponsorship_set-0-funding_secured': 'on',
            'sponsorship_set-0-funding_decision_date': str(datetime.date.today()),
        })

    def test_new_coordinator_signs_up_community_to_participate(self):
        """
        This tests submitting a new community to participate in this round.
         - Create a new RoundPage for the upcoming round where the CFP is open
         - Check that the community CFP page shows community participation sign up is open
        """
        current_round = factories.RoundPageFactory(start_from='pingnew')

        self.client.logout()
        response = self.client.get(reverse('community-cfp'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>New communities</h2>', html=True)
        self.assertContains(response, '<a class="btn btn-success" href="{}">Submit community application</a>'.format(reverse('community-participation-rules')), html=True)
        response = self.client.get(reverse('community-participation-rules'))

        # The community participation rules page now requires people to log in
        # So that we can check whether the person is a coordinator for a community
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, settings.LOGIN_URL + '?next={}'.format(reverse('community-participation-rules')))

        # Assume Comrade account sign up works - TODO: test this separately
        coordinator = factories.ComradeFactory()
        self.client.force_login(coordinator.account)

        response = self.client.get(reverse('community-participation-rules'))
        self.assertContains(response, '<input class="btn btn-success" type="submit" value="Submit community application" />', html=True)

        # The community participation page has a form for the community name
        response = self.client.post(reverse('community-participation-rules'), {
            'community_name': 'Debian',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('community-add'))

        new_community_signup_path = reverse('community-add')
        response = self.client.get(new_community_signup_path)

        response = self.client.post(new_community_signup_path, {
            'name': 'Debian',
            'reason_for_participation': 'We want more diversity in our community.',
            'mentorship_programs': 'We have participated in Google Summer of Code since 2013.',
            'approved_license': 'on',
            'no_proprietary_software': 'on',
            'participating_orgs': 'Debian is comprised of volunteers from around the world. Some corporations pay maintainers to participate.',
            'approved_advertising': 'on',
            },
            follow=True,
        )

        # Ensure the Community object and NewCommunity object was created
        community = Community.objects.get(name='Debian')
        newcommunity = NewCommunity.objects.get(community=community)
        coordinatorapproval = CoordinatorApproval.objects.get(
                coordinator=coordinator,
                community=community,
                approval_status=ApprovalStatus.APPROVED)

        new_community_participation_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': community.slug, })
        self.assertRedirects(response, new_community_participation_path)

        # Usage case test continues in test_old_community_participation_signup

    def test_old_coordinator_uses_new_community_form(self):
        """
        This tests submitting a past participating community's
        name to the form that takes sign-ups for the new communities.
        This should not create a new community with the same name as an old community.

        If the community is not currently participating in this cohort,
        the page should redirect to the participation sign-up form.
        """

        # Create the past participating community
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = factories.RoundPageFactory(start_from='pingnew')

        # Log in as the community coordinator
        self.client.logout()
        self.client.force_login(scenario.coordinator.account)

        # Submit the old community name to the new community participation sign up form
        response = self.client.post(reverse('community-participation-rules'), {
            'community_name': 'dEbian ',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse(
            'participation-action',
            kwargs={
                'action': 'submit',
                'round_slug': current_round.slug,
                'community_slug': scenario.participation.community.slug,
        }))

    def test_old_coordinator_uses_new_community_form_to_sign_up_already_participating_community(self):
        """
        This tests submitting a past participating community's
        name to the form that takes sign-ups for the new communities.
        This should not create a new community with the same name as an old community.

        If the community is currently participating in this cohort,
        the page should redirect to the community mentor CFP page (community landing page).
        """

        # Create the currently participating community
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = factories.RoundPageFactory(start_from='pingnew')
        participation = factories.ParticipationFactory(community=scenario.community, participating_round=current_round, approval_status=ApprovalStatus.PENDING)

        self.client.logout()
        self.client.force_login(scenario.coordinator.account)

        # Submit the old community name to the new community participation sign up form
        response = self.client.post(reverse('community-participation-rules'), {
            'community_name': 'dEbian ',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        print(reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, }))
        self.assertRedirects(response, reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, }))

    def submit_failed_community_signup(self, current_round):
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')

        self.client.force_login(scenario.coordinator.account)
        response = self.coordinator_signs_up_community_to_participate(
                reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, }),
                )
        with self.assertRaises(Participation.DoesNotExist):
            p = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug)
        self.assertNotEqual(response.status_code, 302)

    def test_community_participation_signup_too_early(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
           (the past round is currently in week 10 of the internship)
         - Create a new RoundPage for the upcoming round where the CFP hasn't opened
         - Try to submit the community to participate in the round through the form
         - It should fail
        """
        current_round = factories.RoundPageFactory(start_from='pingnew', days_after_today=1)

        self.check_community_signup_marked_closed()
        self.submit_failed_community_signup(current_round)

    def test_community_participation_signup_too_late(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
           (the past round is currently in week 10 of the internship)
         - Create a new RoundPage for the upcoming round where the CFP is closed to new communities
         - Try to submit the community to participate in the round through the form
         - It should fail
        """
        current_round = factories.RoundPageFactory(start_from='lateorgs')

        self.check_community_signup_marked_closed()
        self.submit_failed_community_signup(current_round)

    def test_old_community_participation_signup(self):
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
           - Funding for 2 interns is visible
           - The 'Coordinate for This Community' button is visible to anyone who is not a coordinator
           - The 'Submit a Project Proposal' button is visible
           - The 'Submit an Outreachy Intern Project Proposal' heading is visible
           - The 'Community will participate' button is visible to a coordinator
           - The 'Community will not participate' button is visible to a coordinator
        """
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = factories.RoundPageFactory(start_from='pingnew')

        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        project_submission_path = reverse('project-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        coordinator_signup_path = reverse('coordinatorapproval-action', kwargs={'action': 'submit', 'community_slug': scenario.participation.community.slug, })
        community_does_participate_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        community_does_not_participate_path = reverse('participation-action', kwargs={'action': 'withdraw', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        sponsor_name = 'Software in the Public Interest - Debian'
        sponsor_amount = 13000

        visitors = self.get_visitors_from_past_round(scenario)
        # There should not be a Participation for Debian in the current round yet
        with self.assertRaises(Participation.DoesNotExist):
            p = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug)

        self.client.force_login(scenario.coordinator.account)
        response = self.coordinator_signs_up_community_to_participate(
                reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, }),
                sponsor_name,
                sponsor_amount,
                )
        self.assertEqual(response.status_code, 302)

        # Ensure the database reflects the community sign-up
        participation = Participation.objects.get(community__slug=scenario.participation.community.slug, participating_round__slug=current_round.slug, approval_status=ApprovalStatus.PENDING)
        sponsorship = Sponsorship.objects.get(participation=participation, coordinator_can_update=True, name=sponsor_name, amount=sponsor_amount, funding_secured=True)

        # Make sure the email to the Outreachy organizers was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Approve community participation - Debian')
        self.assertEqual(mail.outbox[0].from_email, organizers)
        self.assertEqual(mail.outbox[0].to, [organizers])
        self.assertIn(community_read_only_path, mail.outbox[0].body)
        self.assertIn('Number of interns funded: 2', mail.outbox[0].body)
        self.assertIn(sponsor_name, mail.outbox[0].body)
        self.assertIn(str(sponsor_amount), mail.outbox[0].body)

        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<span class="badge badge-pill badge-info">Pending Participation</span>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-success">Funded</span>', html=True)
                self.assertContains(response, '<td>This community has funding for 2 interns.</td>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-warning">No Projects</span>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-info">Open to New Projects</span>', html=True)
                if visitor_type != 'coordinator':
                    self.assertContains(response, '<a href="{}" class="btn btn-success">Coordinate for This Community</a>'.format(coordinator_signup_path), html=True)
                self.assertContains(response, '<h2>Submit an Outreachy Intern Project Proposal</h2>', html=True)
                self.assertContains(response, '<a class="btn btn-success" href="{}">Submit a Project Proposal</a>'.format(project_submission_path), html=True)

    def test_increased_sponsorship_old_community_participation_signup(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
         - Create a new RoundPage for the upcoming round
         - Set the sponsorship_per_intern to 10000 USD (default is currently 6500)
         - Submit the community to participate in the round through the form,
           setting the sponsorship to 20000 USD

        Test home/templates/home/community_read_only.html:
         - Check:
           - Check that the participation sign up form mentions the higher sponsorship amount
           - Funding for 2 interns is visible on the community read-only page
           - Email is sent to the Outreachy organizers with the correct number of interns sponsored
        """
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = factories.RoundPageFactory(start_from='pingnew', days_after_today=-1, sponsorship_per_intern=10000)

        sponsor_name = 'Software in the Public Interest - Debian'
        sponsor_amount = 30000

        visitors = self.get_visitors_from_past_round(scenario)

        self.client.force_login(scenario.coordinator.account)
        # Check to make sure the increased funding amount is mentioned on the participation rules page
        response = self.client.get(reverse('community-participation-rules'))
        self.assertContains(response, '<p>Open source communities must find <a href="{}#intern-funding">internship funding</a> ($10,000 USD per intern):</p>'.format(reverse('docs-community')), html=True)

        response = self.client.get(reverse(
            'participation-action',
            kwargs={
                'action': 'submit',
                'round_slug': current_round.slug,
                'community_slug': scenario.participation.community.slug,
        }))
        self.assertContains(response, '<p>All communities must find finding for at least one intern ($10,000 USD):</p>', html=True)
        self.assertContains(response, '<div class="card-footer bg-white">Sponsorship for each intern is $10,000 USD.</div>', html=True)
                        
        response = self.coordinator_signs_up_community_to_participate(
                reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, }),
                sponsor_name,
                sponsor_amount,
                )
        self.assertEqual(response.status_code, 302)

        # Make sure the email to the Outreachy organizers was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Approve community participation - Debian')
        self.assertIn('Number of interns funded: 3', mail.outbox[0].body)
        self.assertIn(sponsor_name, mail.outbox[0].body)
        self.assertIn(str(sponsor_amount), mail.outbox[0].body)

        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<span class="badge badge-pill badge-success">Funded</span>', html=True)
                self.assertContains(response, '<td>This community has funding for 3 interns.</td>', html=True)
        self.client.logout()

    def test_increased_sponsorship_staff_dashboard(self):
        """
        This tests submitting an older community to participate in this round.
         - Create a community that has been approved to participate in a past round
         - Create a new RoundPage for the upcoming round
         - Set the sponsorship_per_intern to 10000 USD (default is currently 6500)
         - Submit the community to participate in the round through the form,
           setting the sponsorship to 20000 USD

        Test home/templates/home/community_read_only.html:
         - Check:
           - Check that the participation sign up form mentions the higher sponsorship amount
           - Funding for 2 interns is visible on the community read-only page
        """
        current_round = factories.RoundPageFactory(start_from='pingnew', days_after_today=-1, sponsorship_per_intern=10000)
        sponsorship_a = factories.SponsorshipFactory(
                participation__participating_round=current_round,
                participation__approval_status=ApprovalStatus.APPROVED,
                name="Sponsor A",
                amount=30000,
                funding_secured=True,
                )

        # Ensure the community's internship funding shows up correctly on the Outreachy organizer side
        organizer = factories.ComradeFactory()
        organizer.account.is_staff = True
        organizer.account.save()
        self.client.force_login(organizer.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '<td><p>Approved</p><p>3 interns funded</p></td>', html=True)

        self.client.logout()

    def test_community_participation_approval(self):
        """
        This tests approving a community to participate in this round.
         - Create a new RoundPage for the upcoming round, with a pending community
         - Go to the community read-only page
         - Log in as an organizer
         - The community read-only page should have an 'Approve Community' and a 'Reject Community' button
         - Post to the Participation approval URL
         - This should redirect back to community read-only page
         - Participation should now marked as approved in the database
         - Coordinator receives email that the community was approved to participate
         - The community read-only page should now reflect that the community has been approved
           - Community status box should read 'Participating'
         - There should still be a way to submit projects

        Test home/templates/home/community_read_only.html:
         - Check:
           - The 'Participating' status is visible
           - Funding for 1 intern is visible
           - The 'Coordinate for This Community' button is visible to anyone who is not a coordinator
           - The 'Submit a Project Proposal' button is visible
           - The 'Submit an Outreachy Intern Project Proposal' heading is visible
           - The 'Community will participate' button is visible to a coordinator
           - The 'Community will not participate' button is visible to a coordinator
        """
        scenario = scenarios.InternshipWeekScenario(week = 10, community__name='Debian', community__slug='debian')
        current_round = factories.RoundPageFactory(start_from='pingnew')

        community_read_only_path = reverse('community-read-only', kwargs={ 'community_slug': scenario.participation.community.slug, })
        project_submission_path = reverse('project-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        coordinator_signup_path = reverse('coordinatorapproval-action', kwargs={'action': 'submit', 'community_slug': scenario.participation.community.slug, })
        community_does_participate_path = reverse('participation-action', kwargs={'action': 'submit', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        approve_participation_path = reverse('participation-action', kwargs={'action': 'approve', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        reject_participation_path = reverse('participation-action', kwargs={'action': 'reject', 'round_slug': current_round.slug, 'community_slug': scenario.participation.community.slug, })
        visitors = self.get_visitors_from_past_round(scenario)

        # Set up the community with a pending participation in the current round
        participation = factories.ParticipationFactory(community=scenario.community, participating_round=current_round, approval_status=ApprovalStatus.PENDING)
        sponsorship = factories.SponsorshipFactory(participation=participation, name='Software in the Public Interest - Debian', amount=13000)
        
        organizer_account = User.objects.get(is_staff=True)
        self.client.force_login(organizer_account)

        # Double check that the community read-only page has links to approve or reject
        response = self.client.get(community_read_only_path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge badge-pill badge-info">Pending Participation</span>', html=True)
        self.assertContains(response, '<input type="submit" class="btn btn-success m-2" value="Approve Community" />', html=True)
        self.assertContains(response, '<a href="{}" class="btn btn-warning m-2">Reject Community</a>'.format(reject_participation_path), html=True)

        # Approve the community
        response = self.client.post(approve_participation_path)
        self.assertEqual(response.status_code, 302)

        # Check the database status
        approved_participation = Participation.objects.get(community__slug=participation.community.slug, participating_round__slug=current_round.slug, approval_status=ApprovalStatus.APPROVED)

        # Check that the email to the community coordinator was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '{} is participating in Outreachy!'.format(scenario.community.name))
        self.assertEqual(mail.outbox[0].from_email, organizers)
        self.assertEqual(mail.outbox[0].to, scenario.community.get_coordinator_email_list())
        self.assertIn('The Outreachy organizers have approved {} to participate in the current round of Outreachy!'.format(scenario.community.name), mail.outbox[0].body)
        # TODO: we should probably check that other information is correct,
        # like the round dates, but this is enough for now.

        # Check that the community read-only page reflects the database status
        for visitor_type, visitor in visitors:
            with self.subTest(visitor_type=visitor_type):
                self.client.logout()
                if visitor:
                    self.client.force_login(visitor)
                response = self.client.get(community_read_only_path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<span class="badge badge-pill badge-success">Participating</span>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-success">Funded</span>', html=True)
                self.assertContains(response, '<td>This community has funding for 2 interns.</td>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-warning">No Projects</span>', html=True)
                self.assertContains(response, '<span class="badge badge-pill badge-info">Open to New Projects</span>', html=True)
                if visitor_type != 'coordinator':
                    self.assertContains(response, '<a href="{}" class="btn btn-success">Coordinate for This Community</a>'.format(coordinator_signup_path), html=True)
                self.assertContains(response, '<h2>Submit an Outreachy Intern Project Proposal</h2>', html=True)
                self.assertContains(response, '<a class="btn btn-success" href="{}">Submit a Project Proposal</a>'.format(project_submission_path), html=True)

    def test_increased_sponsorship_cfp_announce_email(self):
        """
        This tests whether the email Outreachy organizers should send to the mentor mailing list
        to announce the call for community participation is open is correct:
         - Create a new RoundPage for the upcoming round
         - Set the sponsorship_per_intern to 10000 USD (default is currently 6500)

        Test home/templates/home/email/cfp-open.txt:
         - Check:
           - the email reminder shows up on the staff dashboard
           - the intern sponsorship amount mentioned in the email is correct
        """
        current_round = factories.RoundPageFactory(start_from='pingnew', days_after_today=-1, sponsorship_per_intern=10000)

        organizer = factories.ComradeFactory()
        organizer.account.is_staff = True
        organizer.account.save()
        self.client.force_login(organizer.account)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, "<p>Announce the new round dates internally. Send an email to the mentors' mailing list:</p>", html=True)
        # I have no idea how home/email.py generates URLs for the reminder emails
        email_preview_url = '/{}/email/cfp-open/'.format(current_round.slug)
        response = self.client.get(email_preview_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Each community coordinator will need to secure funding for at least one intern ($10000 USD).", html=False)

        self.client.logout()
