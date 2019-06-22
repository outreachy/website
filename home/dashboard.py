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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.mail.backends.base import BaseEmailBackend
from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
import datetime

from . import email
from .mixins import ComradeRequiredMixin
from .models import ApplicantApproval
from .models import ApprovalStatus
from .models import Community
from .models import Comrade
from .models import DASHBOARD_MODELS
from .models import MentorApproval
from .models import MentorRelationship
from .models import Participation
from .models import Project
from .models import Role
from .models import RoundPage
from .models import get_deadline_date_for
from .models import has_deadline_passed

__all__ = ('get_dashboard_sections',)

def get_dashboard_sections(request):
    now = datetime.datetime.now(datetime.timezone.utc)
    today = get_deadline_date_for(now)

    sections = []
    for section in DASHBOARD_SECTIONS:
        context = section(request, today)
        if context:
            template_name = "home/dashboard/{}.html".format(section.__name__)
            sections.append((template_name, context))
    return sections


def intern_announcement(request, today):
    try:
        # Find the newest round whose intern announcement date has passed.
        current_round = RoundPage.objects.filter(
            internannounce__lte=today,
        ).latest('internannounce')
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    # Hide this message once the next round starts, where "starts" is defined
    # by pingnew, and "next round" means it has a later intern announcement
    # date than this one.
    later_open_rounds = RoundPage.objects.filter(
        pingnew__lte=today,
        internannounce__gt=current_round.internannounce,
    )
    if later_open_rounds.exists():
        return None

    roles = []
    if current_round.is_coordinator(request.user):
        roles.append("coordinator")
    if current_round.is_mentor(request.user):
        roles.append("mentor")
    if request.user.is_staff:
        roles.append("organizer")

    if not roles:
        return None

    return {
        'current_round': current_round,
        'role': ' and '.join(roles),
    }


def coordinator_reminder(request, today):
    # It's possible that some intern selections may not work out, and a mentor
    # will have to select another intern after the intern announcement date.
    # Show coordinator's communities until the day after their mentors' interns
    # start.
    try:
        current_round = RoundPage.objects.filter(
            internstarts__gt=today,
        ).earliest('internstarts')
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    role = Role(request.user, current_round)
    if not role.approved_coordinator_communities:
        return None

    return role


def application_summary(request, today):
    # This should return non-None if, and only if,
    # views.applicant_review_summary doesn't raise an exception like
    # PermissionDenied.

    try:
        current_round = RoundPage.objects.get(
            initial_applications_open__lte=today,
            contributions_open__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    try:
        if not request.user.is_staff and not current_round.is_reviewer(request.user):
            return None
    except Comrade.DoesNotExist:
        return None

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


def staff_subscriptions(request, today):
    # This template doesn't need any data, it just needs to be
    # hidden for non-staff.
    return request.user.is_staff


class RoundEvent(object):
    @classmethod
    def instances(cls):
        return (cls.instance,)

    @classmethod
    def url_name(cls):
        return 'email-' + cls.slug

    @classmethod
    def dashboard_snippet(cls):
        return 'home/dashboard/email/{}.html'.format(cls.slug)


class SendEmailView(RoundEvent, LoginRequiredMixin, ComradeRequiredMixin, BaseEmailBackend, TemplateView):
    template_name = 'home/send_email_preview.html'

    def generate_messages(self, current_round, connection):
        """
        Subclasses must implement this function to generate the desired emails,
        and must pass the connection argument on to the final send_mail or
        send_messages calls.
        """
        pass

    def get_round(self):
        return get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

    def get_context_data(self, **kwargs):
        """
        Use this view's BaseEmailBackend implementation to do a dry-run of
        sending the generated messages, and return a preview of the messages
        that would be sent.
        """
        self.messages = []
        self.generate_messages(current_round=self.get_round(), connection=self)
        context = super(SendEmailView, self).get_context_data(**kwargs)
        context['messages'] = self.messages
        return context

    def send_messages(self, messages):
        """
        Implementation of BaseEmailBackend that just saves the generated
        messages on self, so get_context_data can dig them back out again.
        """
        self.messages.extend(messages)
        return len(messages)

    def post(self, request, *args, **kwargs):
        """
        Use the real email backend to send the generated messages.
        """
        with mail.get_connection() as connection:
            self.generate_messages(current_round=self.get_round(), connection=connection)
        return redirect(reverse('dashboard'))


class MentorCheckDeadlinesReminder(SendEmailView):
    description = 'Mentor Deadlines Email'
    slug = 'deadline-review'

    @staticmethod
    def instance(current_round):
        return current_round.contributions_close - datetime.timedelta(weeks=2)

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        projects = Project.objects.filter(
            approval_status__in=[Project.APPROVED, Project.PENDING],
            project_round__participating_round=current_round,
        )
        for p in projects:
            email.project_applicant_review(p, self.request, connection=connection)


class MentorApplicationDeadlinesReminder(SendEmailView):
    description = 'Mentor Deadline Email'
    slug = 'mentor-application-deadline-reminder'

    @staticmethod
    def instance(current_round):
        # Warn on a Monday at least 3 days before contributions_close:
        due = current_round.contributions_close - datetime.timedelta(days=3)
        due -= datetime.timedelta(days=due.weekday())
        return due

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Don't ask mentors to encourage interns to apply if it's too late for
        # anyone to apply any more.
        if current_round.has_application_deadline_passed():
            return

        projects = Project.objects.filter(project_round__participating_round=current_round).approved()

        for p in projects:
            email.mentor_application_deadline_reminder(p, self.request, connection=connection)

class MentorInternSelectionReminder(SendEmailView):
    description = 'Mentor Intern Selection Email'
    slug = 'mentor-intern-selection-reminder'

    @staticmethod
    def instance(current_round):
        return current_round.contributions_close

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        projects = Project.objects.approved().filter(
            project_round__participating_round=current_round,
        )

        for p in projects:
            email.send_group_template_mail('home/email/mentor-choose-intern.txt', {
                'project': p,
                },
                request=self.request,
                recipient_list=p.get_mentor_email_list(),
                connection=connection)

class CoordinatorInternSelectionReminder(SendEmailView):
    description = 'Coordinator Intern Selection Email'
    slug = 'coordinator-intern-selection-reminder'

    @staticmethod
    def instance(current_round):
        return current_round.contributions_close

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        for p in current_round.participation_set.approved():
            email.coordinator_intern_selection_reminder(p, self.request, connection=connection)


class ApplicantsDeadlinesReminder(SendEmailView):
    description = 'Applicant Deadline Email'
    slug = 'deadline-reminder'

    @staticmethod
    def instance(current_round):
        return MentorCheckDeadlinesReminder.instance(current_round) + datetime.timedelta(days=3)

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        projects = Project.objects.filter(
            project_round__participating_round=current_round,
        ).approved().order_by('project_round__community__name')

        closed_projects = projects.filter(new_contributors_welcome=False)
        email.applicant_deadline_reminder(closed_projects, current_round, self.request, connection=connection)


class ContributorsApplicationPeriodEndedReminder(SendEmailView):
    """
    Email reminder to every applicant who made a contribution.
    This tells them which projects they made a final application to,
    and when to expect interns be announced.
    """
    description = 'Contributor Final Email'
    slug = 'application-period-ended'

    @staticmethod
    def instance(current_round):
        return current_round.contributions_close

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        contributors = Comrade.objects.filter(
            applicantapproval__application_round=current_round,
            applicantapproval__approval_status=ApprovalStatus.APPROVED,
            applicantapproval__contribution__isnull=False).distinct()

        for c in contributors:
            email.contributor_application_period_ended(
                c,
                current_round,
                self.request,
                connection=connection,
            )


class ContributorsDeadlinesReminder(SendEmailView):
    description = 'Contributor Deadline Email'
    slug = 'contributor-deadline-reminder'

    @staticmethod
    def first_reminder(current_round):
        return current_round.contributions_close - datetime.timedelta(weeks=1)

    @staticmethod
    def second_reminder(current_round):
        return current_round.contributions_close - datetime.timedelta(days=1)

    @classmethod
    def instances(cls):
        return (cls.first_reminder, cls.second_reminder)

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        contributors = Comrade.objects.filter(
            applicantapproval__application_round=current_round,
            applicantapproval__approval_status=ApprovalStatus.APPROVED,
        ).distinct()
        if not current_round.has_application_deadline_passed():
            contributors = contributors.filter(applicantapproval__contribution__isnull=False)
        else:
            return

        for c in contributors:
            email.contributor_deadline_reminder(
                c,
                current_round,
                self.request,
                connection=connection,
            )


class InternNotification(SendEmailView):
    description = 'Intern Welcome Email'
    slug = 'intern-welcome'

    @staticmethod
    def instance(current_round):
        return current_round.internannounce

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        interns = current_round.get_approved_intern_selections()

        for i in interns:
            email.notify_accepted_intern(i, self.request, connection=connection)


class InternWeek(SendEmailView):
    @classmethod
    def at(cls, week):
        # Create a subclass of this class where the week number is hard-coded.
        return type('{}{}'.format(cls.__name__, week), (cls,), {
            'week': week,
            'description': 'Week {} Email'.format(week),
            'slug': 'internship-week-{}'.format(week),
        })

    @classmethod
    def instance(cls, current_round):
        return current_round.internstarts + datetime.timedelta(weeks=cls.week - 1)

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        template = 'home/email/internship-week-{}.txt'.format(self.week)
        interns = current_round.get_in_good_standing_intern_selections()

        for i in interns:
            email.biweekly_internship_email(i, self.request, template, connection=connection)


class FeedbackInstructions(SendEmailView):
    @classmethod
    def make_instance(cls, week):
        def instance(current_round):
            return cls.due_date(current_round) + datetime.timedelta(weeks=week)
        return instance

    @classmethod
    def instances(cls):
        # Start sending instructions one week before the standard due date, and
        # continue until four weeks after.
        return tuple(map(cls.make_instance, range(-1, 5)))


class InitialFeedbackInstructions(FeedbackInstructions):
    description = 'Initial Feedback Reminder'
    slug = 'initial-feedback-instructions'

    @staticmethod
    def due_date(current_round):
        return current_round.initialfeedback

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_initial_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "initial", i.is_initial_feedback_on_intern_past_due(), connection=connection)


class MidpointFeedbackInstructions(FeedbackInstructions):
    description = 'Midpoint Feedback Reminder'
    slug = 'midpoint-feedback-instructions'

    @staticmethod
    def due_date(current_round):
        return current_round.midfeedback

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_midpoint_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "midpoint", i.is_midpoint_feedback_on_intern_past_due(), connection=connection)


class FinalFeedbackInstructions(FeedbackInstructions):
    description = 'Final Feedback Reminder'
    slug = 'final-feedback-instructions'

    @staticmethod
    def due_date(current_round):
        return current_round.finalfeedback

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_final_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "final", i.is_final_feedback_on_intern_past_due(), connection=connection)


# This is a list of all reminders that staff need at different times in the
# round. Each entry should be a subclass of both RoundEvent and View.
#
# It doesn't matter what order this list is in, but I think it's less confusing
# if we keep it sorted by when in the round each event occurs.
all_round_events = (
    MentorCheckDeadlinesReminder,
    ApplicantsDeadlinesReminder,
    ContributorsDeadlinesReminder,
    MentorApplicationDeadlinesReminder,
    MentorInternSelectionReminder,
    CoordinatorInternSelectionReminder,
    ContributorsApplicationPeriodEndedReminder,
    InternNotification,
    InternWeek.at(week=1),
    InitialFeedbackInstructions,
    InternWeek.at(week=3),
    InternWeek.at(week=5),
    InternWeek.at(week=7),
    InternWeek.at(week=9),
    MidpointFeedbackInstructions,
    FinalFeedbackInstructions,
)

def round_events(request, today):
    if not request.user.is_staff:
        return None

    # How long before and after the ideal date should we display each reminder?
    early = datetime.timedelta(weeks=2)
    late = datetime.timedelta(weeks=1)

    # Check all rounds for events. Most rounds won't have any
    # currently-relevant events, but there will never be so many rounds that
    # this becomes a performance bottleneck, and it's a lot easier to
    # understand this way than trying to craft a more precise query.
    events = []
    for current_round in RoundPage.objects.order_by():
        for event in all_round_events:
            # If this event has multiple instances, pick the one whose due date
            # is closest to today.
            due = min(
                (due(current_round) for due in event.instances()),
                key=lambda due: abs(today - due),
            )

            if due - early <= today <= due + late:
                events.append({
                    'kind': event,
                    'current_round': current_round,
                    'due': due,
                })

    if events:
        events.sort(key=lambda d: d['due'])
        return {
            'events': events,
            'today': today,
        }


def sponsor_statistics(request, today):
    if not request.user.is_staff:
        return None

    try:
        current_round = RoundPage.objects.filter(
            initial_applications_open__lte=today,
        ).latest('initial_applications_open')
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    return current_round


def staff_intern_progress(request, today):
    if not request.user.is_staff:
        return None

    try:
        current_round = RoundPage.objects.get(
            initialfeedback__lte=today + datetime.timedelta(days=7),
            finalfeedback__gt=today - datetime.timedelta(days=30),
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    return current_round


def staff_intern_selection(request, today):
    if not request.user.is_staff:
        return None

    try:
        # There can't be any interns selected until they start making
        # contributions, so don't display this section until then.
        current_round = RoundPage.objects.get(
            contributions_open__lte=today,
            initialfeedback__gt=today + datetime.timedelta(days=7),
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    return current_round


def staff_community_progress(request, today):
    if not request.user.is_staff:
        return None

    try:
        # Show staff this table as soon as communities can start applying to
        # participate in a round, but nothing in it is relevant any more after
        # interns are announced.
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            internannounce__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    pending_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.PENDING).order_by('community__name')
    approved_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.APPROVED).order_by('community__name')
    participations = list(pending_participations) + list(approved_participations)

    if not participations:
        return None

    return {
        'current_round': current_round,
        'participations': participations,
    }


def selected_intern(request, today):
    try:
        intern_selection = request.user.comrade.get_intern_selection()
    except Comrade.DoesNotExist:
        return None
    if not intern_selection:
        return None

    # No peeking! Wait for the announcement!
    current_round = intern_selection.round()
    current_round.today = today
    if not current_round.has_intern_announcement_deadline_passed():
        return None

    # We could check here how long ago this intern's round was, and
    # maybe remove this section from their dashboard, if desired.

    return intern_selection


def intern(request, today):
    # TODO: move this function somewhere common
    # or TODO: merge with selected_intern above
    # This import can't be at top-level because views.py imports this
    # file so that would be a circular dependency.
    from .views import intern_in_good_standing
    return intern_in_good_standing(request.user)


def eligibility_prompts(request, today):
    try:
        current_round = RoundPage.objects.get(
            appsopen__lte=today,
            internannounce__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    return Role(request.user, current_round)


def unselected_intern(request, today):
    """
    Display a message for people who filled out the eligibility form
    but didn't get selected. But only display it once the
    internannounce deadline has passed, and make the sad message go
    away a few weeks later when the selected interns start working on
    their internships.
    """
    try:
        applicant = ApplicantApproval.objects.exclude(
            internselection__organizer_approved=True,
        ).select_related('application_round').get(
            applicant__account=request.user,
            application_round__internannounce__lte=today,
            application_round__internstarts__gte=today,
        )
        applicant.application_round.today = today
    except ApplicantApproval.DoesNotExist:
        return None

    return applicant


def mentor(request, today):
    return MentorRelationship.objects.filter(mentor__mentor__account=request.user)


def mentor_projects(request, today):
    try:
        comrade = request.user.comrade
    except Comrade.DoesNotExist:
        return None

    # It's possible that some intern selections may not work out,
    # and a mentor will have to select another intern
    # after the intern announcement date.
    # Show their project until the day after their intern starts.
    try:
        current_round = RoundPage.objects.filter(
            internstarts__gt=today,
        ).earliest('internstarts')
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    # Get all projects where they're an approved mentor
    # XXX: previous comment said "where the project is pending," but this is not true; should it be?
    # and the community is approved or pending for the current round.
    # Don't count withdrawn or rejected communities.
    mentored_projects = comrade.get_mentored_projects().filter(
        project_round__participating_round=current_round,
        project_round__approval_status__in=(ApprovalStatus.PENDING, ApprovalStatus.APPROVED),
    )
    if not mentored_projects:
        return None

    # Communities where this person is an approved mentor for at least one
    # approved project, and the community is approved to participate in the
    # current round.

    mentored_communities = Community.objects.filter(
        participation__participating_round=current_round,
        participation__approval_status=ApprovalStatus.APPROVED,
        participation__project__approval_status=ApprovalStatus.APPROVED,
        participation__project__mentorapproval__mentor=comrade,
        participation__project__mentorapproval__approval_status=ApprovalStatus.APPROVED,
    ).distinct()

    return {
        'current_round': current_round,
        'mentored_projects': mentored_projects,
        'mentored_communities': mentored_communities,
    }


def approval_status(request, today):
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
    intern_announcement,
    coordinator_reminder,
    application_summary,
    staff_subscriptions,
    round_events,
    sponsor_statistics,
    staff_intern_progress,
    staff_intern_selection,
    staff_community_progress,
    selected_intern,
    intern,
    eligibility_prompts,
    unselected_intern,
    mentor,
    mentor_projects,
    approval_status,
)
