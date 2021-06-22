import datetime
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from reversion.models import Version

from . import models
from .factories import *
from home import scenarios
from home.email import organizers

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InternSelectionTestCase(TestCase):
    def test_intern_selection_process(self):
        for phase in ('contributions_open', 'contributions_close'):
            with self.subTest(phase=phase):
                current_round = RoundPageFactory(start_from=phase)
                applicantapproval = ApplicantApprovalFactory(
                    application_round=current_round,
                    approval_status=models.ApprovalStatus.APPROVED,
                )

                project = ProjectFactory(
                    project_round__participating_round=current_round,
                    approval_status=models.ApprovalStatus.APPROVED,
                    project_round__approval_status=models.ApprovalStatus.APPROVED,
                )

                finalapplication = FinalApplicationFactory(
                    round=current_round, project=project, applicant=applicantapproval
                )

                mentorapproval = MentorApprovalFactory(
                    project=project, approval_status=models.ApprovalStatus.APPROVED
                )

                coordinatorapproval = CoordinatorApprovalFactory(
                    community=project.project_round.community,
                    approval_status=models.ApprovalStatus.APPROVED,
                )

                organizer = ComradeFactory(account__is_staff=True).account

                post_params = {
                    "round_slug": current_round.slug,
                    "community_slug": project.project_round.community.slug,
                    "project_slug": project.slug,
                    "applicant_username": applicantapproval.applicant.account.username,
                }

                # mentor selects the intern..
                self.client.force_login(mentorapproval.mentor.account)
                path = reverse("select-intern", kwargs={**post_params})

                legal_name = mentorapproval.mentor.public_name
                response = self.client.post(path, {
                    "rating-rating": models.FinalApplication.AMAZING,
                    "contract-legal_name": legal_name,
                })
                self.assertEqual(response.status_code, 302)

                new_relationship = models.MentorRelationship.objects.get(mentor=mentorapproval)
                intern_selection = new_relationship.intern_selection
                self.assertEqual(new_relationship.contract.legal_name, legal_name)
                self.assertEqual(intern_selection.applicant, applicantapproval)
                self.assertEqual(intern_selection.project, project)

                # organizer approves too early, rejected..
                self.client.force_login(organizer)
                path = reverse("intern-approval", kwargs={
                    **post_params,
                    "approval": "Approved",
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 403)
                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.organizer_approved, None)

                # coordinator adds funding..
                self.client.force_login(coordinatorapproval.coordinator.account)
                path = reverse("intern-fund", kwargs={
                    **post_params,
                    "funding": models.InternSelection.GENERAL_FUNDED,
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.funding_source, models.InternSelection.GENERAL_FUNDED)

                # organizer approves..
                self.client.force_login(organizer)
                path = reverse("intern-approval", kwargs={
                    **post_params,
                    "approval": "Approved",
                })
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                intern_selection = models.InternSelection.objects.get(project=project)
                self.assertEqual(intern_selection.organizer_approved, True)

    def test_intern_selection_emails(self):
        scenario = scenarios.ContributionsClosedScenario()

        rejected_mentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.REJECTED
        )
        withdrawn_mentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.WITHDRAWN
        )
        approved_comentor = MentorApprovalFactory(
            project=scenario.project, approval_status=models.ApprovalStatus.APPROVED
        )

        post_params = {
            "round_slug": scenario.round.slug,
            "community_slug": scenario.project.project_round.community.slug,
            "project_slug": scenario.project.slug,
            "applicant_username": scenario.applicant1.applicant.account.username,
        }
        legal_name = scenario.mentor.public_name

        # mentor selects the intern.
        self.client.force_login(scenario.mentor.account)
        path = reverse("select-intern", kwargs={**post_params})
        response = self.client.post(path, {
            "rating-rating": models.FinalApplication.AMAZING,
            "contract-legal_name": legal_name,
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Outreachy intern selected - please sign mentoring agreement')
        self.assertEqual(mail.outbox[0].from_email, organizers)

        # Check important links are in the email body
        comentor_sign_up_link = reverse('select-intern', kwargs={
            'round_slug': scenario.round.slug,
            'community_slug': scenario.community.slug,
            'project_slug' : scenario.project.slug,
            'applicant_username': scenario.applicant1.applicant.account.username,
        })
        project_applicants_link = reverse('project-applicants', kwargs={
            'round_slug': scenario.round.slug,
            'community_slug': scenario.community.slug,
            'project_slug' : scenario.project.slug,
        })
        self.assertIn(comentor_sign_up_link, mail.outbox[0].body)
        self.assertIn(project_applicants_link, mail.outbox[0].body)
        self.assertIn(reverse('alums'), mail.outbox[0].body)

        # The rejected and withdrawn mentors
        # should not get an email about the intern selection,
        # but the approved co-mentor should get an email.
        self.assertEqual(mail.outbox[0].to, [approved_comentor.mentor.email_address()])

    def test_mentor_can_resign(self):
        current_round = RoundPageFactory(start_from='midfeedback')
        for mentors_count in (1, 2):
            with self.subTest(mentors_count=mentors_count):
                internselection = InternSelectionFactory(
                    active=True,
                    mentors=mentors_count,
                    round=current_round,
                )
                mentors = list(internselection.mentors.all())
                mentor = mentors.pop()

                path = reverse('resign-as-mentor', kwargs={
                    'round_slug': internselection.round().slug,
                    'community_slug': internselection.project.project_round.community.slug,
                    'project_slug': internselection.project.slug,
                    'applicant_username': internselection.applicant.applicant.account.username,
                })

                self.client.force_login(mentor.mentor.account)
                response = self.client.post(path)
                self.assertEqual(response.status_code, 302)

                self.assertQuerysetEqual(internselection.mentors.all(), mentors, transform=lambda x: x)

