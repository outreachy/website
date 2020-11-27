from .models import ApprovalStatus, DASHBOARD_MODELS

def header(request):
    if request.user.is_authenticated:
        # TODO: don't count objects where the submission_and_approval_deadline has passed
        pending_approvals = sum(
            model.objects_for_dashboard(request.user).pending().distinct().count()
            for model in DASHBOARD_MODELS
        )
    else:
        pending_approvals = 0

    return {
        'pending_approvals': pending_approvals,
    }
