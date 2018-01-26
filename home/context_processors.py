from wagtail.wagtailcore.models import Page
from .models import ApprovalStatus, DASHBOARD_MODELS

def header(request):
    if request.user.is_authenticated:
        pending_approvals = sum(
                model.objects_for_dashboard(request.user).filter(approval_status=ApprovalStatus.PENDING).distinct().count()
                for model in DASHBOARD_MODELS)
    else:
        pending_approvals = 0

    return {
            'header_pages': Page.objects.live().in_menu(),
            'pending_approvals': pending_approvals,
            }
