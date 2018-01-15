from wagtail.wagtailcore.models import Page
from . import models

def header(request):
    dashboard_models = (
            models.CoordinatorApproval,
            models.Participation,
            models.Project,
            models.MentorApproval,
            )

    if request.user.is_authenticated:
        pending_approvals = sum(
                model.objects_for_dashboard(request.user).filter(approval_status=models.ApprovalStatus.PENDING).distinct().count()
                for model in dashboard_models)
    else:
        pending_approvals = 0

    return {
            'header_pages': Page.objects.live().in_menu(),
            'pending_approvals': pending_approvals,
            }
