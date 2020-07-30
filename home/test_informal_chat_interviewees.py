import datetime
import factory
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
class InformalChatContactsTestCase(TestCase):
    '''
    This class tests whether the following people
    have access to the informal chat contacts page:
      - DENIED - Comrade not logged in
      - DENIED - Comrade logged in, but NOT an intern or mentor
      - APPROVED - Intern logged in, who is in good standing
      - DENIED - Intern logged in, who is NOT in good standing
      - APPROVED - Alum logged in, who is in good standing
      - DENIED - Alum logged in, who is NOT in good standing
      - APPROVED - Mentor logged in, who is a mentor of an intern in good standing
      - DENIED - Mentor logged in, but NOT mentoring an intern in good standing
      - APPROVED - Approved coordinator logged in, whose community has been approved to participate
      - DENIED - Approved coordinator logged in, whose community has NOT been approved to participate
      - APPROVED - Staff
    '''

    def assert_permission_denied_on_informal_chat_contacts(self):
        response = self.client.get(reverse('informal-chat-contacts'))
        self.assertEqual(response.status_code, 403)

    def assert_permission_approved_on_informal_chat_contacts(self):
        response = self.client.get(reverse('informal-chat-contacts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Informal Chat Contacts</h1>', html=True)

    def test_not_logged_in(self):
        """
        This tests that informal chat contracts are not visible to someone who is not logged in.
        """

        self.client.logout()
        response = self.client.get(reverse('informal-chat-contacts'))
        self.assertEqual(response.status_code, 302)


    def test_not_authorized_and_logged_in(self):
        """
        This tests that informal chat contracts are not visible to someone who is logged in, but not authorized to see them.
        """

        scenario = scenarios.InternshipWeekScenario(week=11)

        # Applicant 4 has a pending initial application
        # and should not be able to see the informal chat contacts
        self.client.force_login(scenario.applicant4.applicant.account)

        self.assert_permission_denied_on_informal_chat_contacts()

    def test_mentor_with_no_intern_and_logged_in(self):
        """
        This tests that informal chat contracts are not visible to a mentor who is logged in, but does not have an organizer approved intern.
        """

        scenario = scenarios.InternshipWeekScenario(week=11)
        scenario.intern_selection = factories.InternSelectionFactory(
            round=scenario.round,
            funding_source=models.InternSelection.ORG_FUNDED,
            organizer_approved=False,
        )

        # The unapproved intern's mentor
        # should not be able to see the informal chat contacts
        mentors = models.MentorRelationship.objects.filter(intern_selection=scenario.intern_selection)
        self.client.force_login(mentors[0].mentor.mentor.account)

        self.assert_permission_denied_on_informal_chat_contacts()

    def test_intern_in_good_standing_and_logged_in(self):
        """
        This tests that informal chat contracts are visible to an intern who is logged in, but not authorized to see them.
        """

        scenario = scenarios.InternshipWeekScenario(week=11)

        # Applicant 1 is an approved intern
        # and should be able to see the informal chat contacts
        self.client.force_login(scenario.applicant1.applicant.account)

        self.assert_permission_approved_on_informal_chat_contacts()

    def test_intern_in_bad_standing_and_logged_in(self):
        """
        This tests that informal chat contracts are visible to an intern who is logged in, but not authorized to see them.
        """

        scenario = scenarios.InternshipWeekScenario(week=11)
        scenario.intern_selection1.in_good_standing = False
        scenario.intern_selection1.save()

        # Applicant 1 is an approved intern who is not in good standing
        # and should not be able to see the informal chat contacts
        self.client.force_login(scenario.applicant1.applicant.account)

        self.assert_permission_denied_on_informal_chat_contacts()

    def test_mentor_with_intern_and_logged_in(self):
        """
        This tests that informal chat contracts are visible to a mentor who is logged in, who does have an organizer approved intern.
        """

        scenario = scenarios.InternshipWeekScenario(week=11)

        # Mentor 1 is mentoring Applicant 1 (who is an approved intern)
        # and should be able to see the informal chat contacts
        mentors = models.MentorRelationship.objects.filter(intern_selection=scenario.intern_selection1)
        self.client.force_login(mentors[0].mentor.mentor.account)

        self.assert_permission_approved_on_informal_chat_contacts()

    def test_approved_coordinator_logged_in(self):
        '''
        This tests that informal chat contracts are visible to an approved coordinator logged in, whose community has been approved to participate
        '''
        scenario = scenarios.InternshipWeekScenario(week=11)
        self.client.force_login(scenario.coordinator.account)
        self.assert_permission_approved_on_informal_chat_contacts()

    def test_approved_coordinator_unapproved_community_logged_in(self):
        '''
        This tests that informal chat contracts are NOT visible to an approved coordinator logged in, whose community has NOT been approved to participate
        '''
        scenario = scenarios.InternshipWeekScenario(week=11)
        for community_approval_status in [models.ApprovalStatus.PENDING, models.ApprovalStatus.WITHDRAWN, models.ApprovalStatus.REJECTED]:
            with self.subTest(community_approval_status=community_approval_status):
                scenario.participation.approval_status = community_approval_status
                scenario.participation.save()
                self.client.force_login(scenario.coordinator.account)
                self.assert_permission_denied_on_informal_chat_contacts()
                self.client.logout()

    def test_unapproved_coordinator_approved_community_logged_in(self):
        '''
        This tests that informal chat contracts are NOT visible to an unapproved coordinator logged in, whose community has NOT been approved to participate
        '''
        scenario = scenarios.NewRoundScenario(round__start_from='internends', round__days_after_today = -185)
        for coordinator_approval_status in [models.ApprovalStatus.PENDING, models.ApprovalStatus.WITHDRAWN, models.ApprovalStatus.REJECTED]:
            with self.subTest(coordinator_approval_status=coordinator_approval_status):
                participation = factories.ParticipationFactory(
                        participating_round=scenario.round,
                        approval_status=models.ApprovalStatus.APPROVED,
                        )
                coordinator_approval = factories.CoordinatorApprovalFactory(
                        community=participation.community,
                        approval_status=coordinator_approval_status,
                        )
                self.client.force_login(coordinator_approval.coordinator.account)
                self.assert_permission_denied_on_informal_chat_contacts()
                self.client.logout()

    def test_unapproved_coordinator_unapproved_community_logged_in(self):
        '''
        This tests that informal chat contracts are NOT visible to an unapproved coordinator logged in, whose community has NOT been approved to participate
        '''
        scenario = scenarios.NewRoundScenario(round__start_from='internends', round__days_after_today = -185)
        for community_approval_status in [models.ApprovalStatus.PENDING, models.ApprovalStatus.WITHDRAWN, models.ApprovalStatus.REJECTED]:
            with self.subTest(community_approval_status=community_approval_status):
                for coordinator_approval_status in [models.ApprovalStatus.PENDING, models.ApprovalStatus.WITHDRAWN, models.ApprovalStatus.REJECTED]:
                    with self.subTest(coordinator_approval_status=coordinator_approval_status):
                        participation = factories.ParticipationFactory(
                                participating_round=scenario.round,
                                approval_status=community_approval_status,
                                )
                        coordinator_approval = factories.CoordinatorApprovalFactory(
                                community=participation.community,
                                approval_status=coordinator_approval_status,
                                )
                        self.client.force_login(coordinator_approval.coordinator.account)
                        self.assert_permission_denied_on_informal_chat_contacts()
                        self.client.logout()

    def test_alum_in_good_standing_and_logged_in(self):
        """
        This tests that informal chat contracts are visible to an intern who is logged in and is authorized to see them.
        """

        scenario = scenarios.NewRoundScenario(round__start_from='internends', round__days_after_today = -185)
        scenario.intern_selection = factories.InternSelectionFactory(
            round=scenario.round,
            funding_source=models.InternSelection.ORG_FUNDED,
            organizer_approved=True,
            in_good_standing=True,
        )

        # Applicant 1 is an approved alum in a past round in good standing
        # and should not be able to see the informal chat contacts
        self.client.force_login(scenario.intern_selection.applicant.applicant.account)

        self.assert_permission_approved_on_informal_chat_contacts()

    def test_alum_in_bad_standing_and_logged_in(self):
        """
        This tests that informal chat contracts are NOT visible to an intern who is logged in, but not authorized to see them.
        """

        scenario = scenarios.NewRoundScenario(round__start_from='internends', round__days_after_today = -185)
        scenario.intern_selection = factories.InternSelectionFactory(
            round=scenario.round,
            funding_source=models.InternSelection.ORG_FUNDED,
            organizer_approved=False,
            in_good_standing=False,
        )

        # The alum is an approved intern who is not in good standing
        # and should not be able to see the informal chat contacts
        self.client.force_login(scenario.intern_selection.applicant.applicant.account)

        self.assert_permission_denied_on_informal_chat_contacts()

    def test_staff_and_logged_in(self):
        """
        This tests that informal chat contracts are visible to staff who is logged in
        """

        staff = factories.ComradeFactory(account__is_staff=True)

        self.client.force_login(staff.account)
        self.assert_permission_approved_on_informal_chat_contacts()

    def test_active_contact(self):
        """
        This tests that active informal chat contracts are visible to staff who is logged in
        """

        contact = models.InformalChatContact(
                active=True,
                name="Given Name Family Names",
                email="volunteer@example.com",
                )
        contact.save()

        staff = factories.ComradeFactory(account__is_staff=True)
        self.client.force_login(staff.account)
        response = self.client.get(reverse('informal-chat-contacts'))
        self.assertContains(response, '<div class="card-header bg-light">{}</div>'.format(contact.name), html=True)

    def test_inactive_contact(self):
        """
        This tests that inactive informal chat contracts are NOT visible to staff who is logged in
        """

        contact = models.InformalChatContact(
                active=False,
                name="Given Name Family Names",
                email="volunteer@example.com",
                )
        contact.save()

        staff = factories.ComradeFactory(account__is_staff=True)
        self.client.force_login(staff.account)
        response = self.client.get(reverse('informal-chat-contacts'))
        self.assertNotContains(response, '<div class="card-header bg-light">{}</div>'.format(contact.name), html=True)
