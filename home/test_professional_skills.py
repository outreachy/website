from django.test import TestCase, override_settings

from .models import *
from home import factories
from home import scenarios

# don't try to use the static files manifest during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProfessionalSkillsTestCase(TestCase):
    def setUp(self):
        self.skill = 'Python'
        self.experience_level = 'EXP'
        self.current_round = factories.RoundPageFactory(start_from='initial_applications_open')
        self.applicant = factories.ApplicantApprovalFactory(
            approval_status=ApprovalStatus.PENDING,
            application_round=self.current_round
        )
        self.client.force_login(self.applicant.applicant.account)
        self.professionalskill_submission_path = reverse('professional-skills')
        self.eligibilityresults_path = reverse('eligibility-results')

    def test_professional_skill_submission(self):
        """
        This tests that a professional skill can be successfully submitted and saved.
        Tests that the skill is saved correctly and the user is redirected to the eligibility results page.
        """
        response = self.client.post(self.professionalskill_submission_path, {
            'professionalskill_set-TOTAL_FORMS': '1',
            'professionalskill_set-INITIAL_FORMS': '0',
            'professionalskill_set-MIN_NUM_FORMS': '0',
            'professionalskill_set-MAX_NUM_FORMS': '5',
            'professionalskill_set-0-skill': self.skill,
            'professionalskill_set-0-experience_level': self.experience_level,
            },
            follow=True,
        )

        professionalskill = ProfessionalSkill.objects.get(
                comrade=self.applicant.applicant,
                skill=self.skill,
                experience_level=self.experience_level,
        )

        self.assertIsNotNone(professionalskill)
        self.assertRedirects(response, self.eligibilityresults_path)

    # - Applicants should be able to see their professional skills on the eligibility results page
    def test_professional_skills_in_eligibility_results_page(self):
        """
        This tests that professional skills are displayed on the eligibility results page.
        """
        response = self.client.get(self.eligibilityresults_path)
        self.assertContains(response, '<div class="card-header text-white bg-secondary">Professional Skills</div>', html=True)
        self.assertEqual(response.status_code, 200)

    # - Mentors should be able to see applicant's professional skills on the project applicants page
    def test_professional_skills_in_project_applicants_page(self):
        """
        This tests that professional skills are displayed on the project applicants page for mentors.
        """
        scenario = scenarios.InternSelectionScenario(
            applicant1__applicant__public_name="Fru It",
            applicant2__applicant__public_name="Oran Ges",
        )
        self.client.logout()
        self.client.force_login(scenario.mentor.account)
        response = self.client.get(reverse('project-applicants', kwargs={
            'round_slug': scenario.round.slug,
            'community_slug': scenario.community.slug,
            'project_slug' : scenario.project.slug,
        }))
        self.assertContains(response, '<div class="card-header text-white bg-secondary">Professional Skills</div>',
                            html=True)
        self.assertEqual(response.status_code, 200)
