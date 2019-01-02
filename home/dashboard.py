"""
To add a new dashboard section, there are three steps:

- Define a function that takes a request and returns a context
  value. If the value evaluates false, like False, None, [], or {},
  then this section will be skipped.

- The name of that function determines what template renders this
  section. For example, the function named "approval_status" gets
  the template named "home/dashboard/approval_status.html". Within
  the template, the section's context value is available under
  the name "section".

- Add the function name to the DASHBOARD_SECTIONS list at the end of
  this file. The order in which functions appear in that list
  determines the order that sections will be displayed on the
  dashboard, so you can reorder them easily.

The context value can be any type. Here are some examples:

- If the function returns {'x': ...}, the template can access that
  as "section.x".

- If it returns a list, then "{% for x in section %}" will loop over
  that list.
"""

from collections import defaultdict

from .models import ApplicantApproval
from .models import ApprovalStatus
from .models import Comrade
from .models import DASHBOARD_MODELS
from .models import MentorRelationship
from .models import Participation
from .models import RoundPage

__all__ = ('get_dashboard_sections',)

def get_dashboard_sections(request):
    sections = []
    for section in DASHBOARD_SECTIONS:
        context = section(request)
        if context:
            template_name = "home/dashboard/{}.html".format(section.__name__)
            sections.append((template_name, context))
    return sections


def application_summary(request):
    try:
        if not request.user.is_staff and not request.user.comrade.approved_reviewer():
            return None
    except Comrade.DoesNotExist:
        return None

    current_round = RoundPage.objects.latest('internstarts')

    pending_revisions_count = ApplicantApproval.objects.filter(
            application_round = current_round,
            approval_status = ApprovalStatus.PENDING,
            barrierstoparticipation__applicant_should_update=True).count() + ApplicantApproval.objects.filter(
                    application_round = current_round,
                    approval_status = ApprovalStatus.PENDING,
                    schoolinformation__applicant_should_update=True).count()

    pending_applications_count = ApplicantApproval.objects.filter(
            application_round = current_round,
            approval_status = ApprovalStatus.PENDING).count() - pending_revisions_count

    rejected_applications_count = ApplicantApproval.objects.filter(
            application_round = current_round,
            approval_status = ApprovalStatus.REJECTED).count()
    approved_applications_count = ApplicantApproval.objects.filter(
            application_round = current_round,
            approval_status = ApprovalStatus.APPROVED).count()

    return {
        'pending_applications_count': pending_applications_count,
        'pending_revisions_count': pending_revisions_count,
        'rejected_applications_count': rejected_applications_count,
        'approved_applications_count': approved_applications_count,
    }


def staff(request):
    if not request.user.is_staff:
        return None

    current_round = RoundPage.objects.latest('internstarts')
    pending_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.PENDING).order_by('community__name')
    approved_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.APPROVED).order_by('community__name')
    participations = list(pending_participations) + list(approved_participations)

    return {
        'current_round': current_round,
        'pending_participations': pending_participations,
        'approved_participations': approved_participations,
        'participations': participations,
    }


def intern(request):
    # XXX: move this function somewhere common
    # This import can't be at top-level because views.py imports this
    # file so that would be a circular dependency.
    from .views import intern_in_good_standing
    return intern_in_good_standing(request.user)


def mentor(request):
    return MentorRelationship.objects.filter(mentor__mentor__account=request.user)


def mentor_projects(request):
    try:
        return request.user.comrade.get_editable_mentored_projects()
    except Comrade.DoesNotExist:
        return None


def approval_status(request):
    """
    Find objects for which the current user is either an approver or a
    submitter, and list them all in one place.
    """
    by_status = defaultdict(list)
    for model in DASHBOARD_MODELS:
        by_model = defaultdict(list)
        for obj in model.objects_for_dashboard(request.user).distinct():
            if obj.approval_status == ApprovalStatus.APPROVED or not has_deadline_passed(obj.submission_and_approval_deadline()):
                by_model[obj.approval_status].append(obj)

        label = model._meta.verbose_name
        for status, objects in by_model.items():
            by_status[status].append((label, objects))

    groups = []
    for status, label in ApprovalStatus.APPROVAL_STATUS_CHOICES:
        group = by_status.get(status)
        if group:
            groups.append((label, group))

    # If this person has nothing to do, groups will be an empty
    # list, which will cause this section to be skipped.
    return groups


DASHBOARD_SECTIONS = (
    application_summary,
    staff,
    intern,
    mentor,
    mentor_projects,
    approval_status,
)
