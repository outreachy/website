from unittest.mock import Mock, patch

from django.test import TestCase

from home import email as module
from home import factories
from home.models import InternSelection


class EmailTests(TestCase):

    @patch.object(module, 'send_group_template_mail')
    def test_intern_selection_conflict_notification(self, mock_send_email):
        project_a = factories.ProjectFactory()
        intern_selection_project_a = factories.InternSelectionFactory(
            project=project_a,
            active=True
        )
        project_b = factories.ProjectFactory(project_round=project_a.project_round)
        intern_selection_project_b = factories.InternSelectionFactory(
            project=project_b,
            applicant=intern_selection_project_a.applicant,
            round=intern_selection_project_a.round(),
            active=True,
        )

        module.intern_selection_conflict_notification(intern_selection_project_b, Mock())
        mock_send_email.called == True
