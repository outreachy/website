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
from django.utils.html import urlize
from django.views.generic import TemplateView
import datetime
import re

from . import email
from .mixins import ComradeRequiredMixin
from .models import ApplicantApproval
from .models import ApplicationReviewer
from .models import ApprovalStatus
from .models import Community
from .models import Comrade
from .models import DASHBOARD_MODELS
from .models import InitialApplicationReview
from .models import MentorApproval
from .models import MentorRelationship
from .models import Participation
from .models import Project
from .models import Role
from .models import RoundPage
from .models import get_deadline_date_for

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
            contributions_close__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    try:
        if not request.user.is_staff and not current_round.is_reviewer(request.user):
            return None
    except Comrade.DoesNotExist:
        return None

    current_applicants = current_round.applicantapproval_set

    pending_applications_count = current_applicants.pending().distinct().count()
    pending_unreviewed_unowned_count = current_applicants.pending().filter(initialapplicationreview__isnull=True, review_owner=None).distinct().count()
    pending_unreviewed_unowned_non_student_count = current_applicants.pending().filter(initialapplicationreview__isnull=True, review_owner=None, schoolinformation__isnull=True).distinct().count()
    pending_reviewed_unowned_count = current_applicants.pending().filter(initialapplicationreview__isnull=False, review_owner=None).distinct().count()

    rejected_applications_count = current_applicants.rejected().distinct().count()
    approved_applications_count = current_applicants.approved().distinct().count()

    reviewed_strong_count = current_applicants.pending().filter(review_owner=None).filter(initialapplicationreview__essay_rating=InitialApplicationReview.STRONG).distinct().count()
    reviewed_good_count = current_applicants.pending().filter(review_owner=None).filter(initialapplicationreview__essay_rating=InitialApplicationReview.GOOD).distinct().count()
    reviewed_maybe_count = current_applicants.pending().filter(review_owner=None).filter(initialapplicationreview__essay_rating=InitialApplicationReview.MAYBE).distinct().count()
    reviewed_unclear_count = current_applicants.pending().filter(review_owner=None).filter(initialapplicationreview__essay_rating=InitialApplicationReview.UNCLEAR).distinct().count()

    reviewers = ApplicationReviewer.objects.filter(reviewing_round=current_round).approved().order_by('comrade__public_name').annotate(number_pending_applications_owned=models.Count('applicantapproval', filter=models.Q(applicantapproval__approval_status=ApprovalStatus.PENDING)))

    return {
        'pending_applications_count': pending_applications_count,
        'pending_unreviewed_unowned_count': pending_unreviewed_unowned_count,
        'pending_unreviewed_unowned_non_student_count': pending_unreviewed_unowned_non_student_count,
        'pending_reviewed_unowned_count': pending_reviewed_unowned_count,
        'reviewed_strong_count': reviewed_strong_count,
        'reviewed_good_count': reviewed_good_count,
        'reviewed_maybe_count': reviewed_maybe_count,
        'reviewed_unclear_count': reviewed_unclear_count,
        'rejected_applications_count': rejected_applications_count,
        'approved_applications_count': approved_applications_count,
        'reviewers': reviewers,
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

        # Find all URLs in all messages by asking Django's urlize function to
        # mark up URL-like text as HTML and then looking for the HTML that
        # urlize generated.
        urlize_re = re.compile(r'<a href="(.*?)"')
        urls = set()
        for message in self.messages:
            for url in urlize_re.finditer(urlize(message.body)):
                urls.add(url.group(1))

        context = super(SendEmailView, self).get_context_data(**kwargs)
        context['messages'] = self.messages
        context['urls'] = sorted(urls)
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
        return redirect('dashboard')

class CFPOpen(SendEmailView):
    """
    Notify the Outreachy mentor's mailing list that community sign-up has started.

    When: The round opens (pingnew)

    Template: home/templates/home/email/cfp-open.txt
    """
    description = 'CFP Open Email'
    slug = 'cfp-open'

    @staticmethod
    def instance(current_round):
        return current_round.pingnew

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        email.cfp_open(current_round, self.request, connection=connection)

class CoordinatorProjectDeadline(SendEmailView):
    """
    Notify Outreachy coordinators that the project deadline is approaching.

    When: 1 week before the project soft deadline

    Template: home/templates/home/email/coordinator-project-deadline.txt
    """
    description = 'Project deadline reminder'
    slug = 'coordinator-project-deadline'

    @staticmethod
    def instance(current_round):
        return current_round.project_soft_deadline() - datetime.timedelta(days=7)

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        # for i in current_round get approved and pending participations:
        participations = current_round.participation_set.exclude(approval_status=ApprovalStatus.WITHDRAWN).exclude(approval_status=ApprovalStatus.REJECTED)
        for p in participations:
            email.coordinator_project_deadline(current_round, p, self.request, connection=connection)


class MentorCheckDeadlinesReminder(SendEmailView):
    """
    Remind mentors that they should consider closing to new applicants.

    When: 2 weeks before the contribution period closes

    Template: home/templates/home/email/mentor-applicant-updates.txt
    """
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
    """
    Warn mentors of the upcoming final application deadline.
    Tell them how to help applicants make a project timeline.
    Tell them which applicants have filled out a final application.
    Link to the page for them to view applicants.

    When: On a Monday 1 week before the final application deadline.
          (Will be at least three days before, not more than 10 days)

    Template: home/templates/home/email/mentor-application-deadline-approaching.txt
    """
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
        if current_round.contributions_close.has_passed():
            return

        projects = Project.objects.filter(project_round__participating_round=current_round).approved()

        for p in projects:
            email.mentor_application_deadline_reminder(p, self.request, connection=connection)

class MentorInternSelectionReminder(SendEmailView):
    """
    Tell mentors how to select an intern.
    Remind them of when the intern selection deadline is.

    When: After the contribution period closes.

    Template: home/templates/home/email/mentor-choose-intern.txt
    """
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
    """
    Tell coordinators how to review intern selections.
    Tell them they need to set the intern funding source.

    When: After the contribution period closes.

    Template: home/templates/home/email/coordinator-intern-selection.txt
    """
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
    """
    Send an email to the Outreachy announcement mailing list.
    Remind everyone about the final application deadline.
    List which projects are closed to new applicants.

    When: Three days after the email to mentors asking them to close
          their projects to new applicants (i.e. 11 days before
          the contribution period ends).

    Template: home/templates/home/email/applicants-deadline-reminder.txt
    """
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

    When: After the final application deadline

    Template: home/templates/home/email/contributors_application_period_ended.txt
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
    """
    Remind all applicants who recorded a contribution to create a final application.

    When: On a Monday, 3 to 10 days before the final application deadline.

    Template: home/templates/home/email/contributors-deadline-reminder.txt
    """
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

        # Don't ask contributors to submit final applications if it's too late
        # for anyone to apply any more.
        if current_round.contributions_close.has_passed():
            return

        contributors = Comrade.objects.filter(
            applicantapproval__application_round=current_round,
            applicantapproval__approval_status=ApprovalStatus.APPROVED,
        ).distinct()

        for c in contributors:
            email.contributor_deadline_reminder(
                c,
                current_round,
                self.request,
                connection=connection,
            )

class MentorInternSelectionDeadlineReminder(SendEmailView):
    """
    Remind mentors who haven't selected an intern of the intern selection deadline.

    When: The day of the intern selection deadline.

    Template: home/templates/home/email/mentor-intern-selection-deadline-reminder.txt
    """
    description = 'Mentor Intern Selection Deadline Reminder'
    slug = 'mentor-intern-selection-deadline-reminder'

    @staticmethod
    def instance(current_round):
        return current_round.mentor_intern_selection_deadline

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Find approved projects for this internship cohort
        # Look for projects that haven't made an intern selection yet
        # Only include projects where:
        #   - An applicant created a final application AND
        #   - At least one final application was unrated, or rated 3 or above
        projects = Project.objects.approved().filter(
            project_round__participating_round=current_round,
            internselection__isnull=True,
            finalapplication__isnull=False
        ).filter(
                models.Q(finalapplication__rating='0')
                | models.Q(finalapplication__rating='3')
                | models.Q(finalapplication__rating='4')
                | models.Q(finalapplication__rating='5')
        ).distinct()

        for p in projects:
            email.mentor_intern_selection_deadline_reminder(p, self.request, connection=connection)

class InternNotification(SendEmailView):
    """
    Individual mail sent to interns notifying them of the internship.

    When: After interns are announced on the website.

    Template: home/templates/home/email/interns-notify.txt
    """
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

class ContractReminder(SendEmailView):
    """
    Individual mail sent to interns who have not signed the internship agreement.

    When: Five days after interns are announced on the website.

    Template: home/templates/home/email/reminder-sign-internship-agreement.txt
    """
    description = 'Reminder to sign internship agreement'
    slug = 'reminder-sign-internship-agreement'

    @staticmethod
    def instance(current_round):
        return current_round.intern_agreement_deadline()

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        interns = current_round.get_approved_intern_selections().filter(intern_contract__isnull=True)

        for i in interns:
            email.reminder_sign_internship_agreement(i, self.request, connection=connection)

class InternWeek(SendEmailView):
    """
    Send chat reminders and blog post prompts.

    When: Every two weeks during the internship.

    Template: home/templates/home/email/internship-week-{}.txt
    """
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
    """
    Send initial feedback instructions to mentors and interns.

    When: When initial feedback forms open, and again if feedback is missing.
          Emails may be sent with an URGENT subject if feedback is late.
          Emails may be sent multiple times if there is a internship extension.

    Templates: home/templates/home/email/initial-feedback-reminder.txt
               home/templates/home/email/initial-feedback-instructions.txt
    """
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
    """
    Send mid-point feedback instructions to mentors and interns.

    When: When mid-point feedback forms open, and again if feedback is missing.
          Emails may be sent with an URGENT subject if feedback is late.
          Emails may be sent multiple times if there is a internship extension.

    Templates: home/templates/home/email/midpoint-feedback-reminder.txt
               home/templates/home/email/midpoint-feedback-instructions.txt
    """
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
            email.feedback_email(i, self.request, "midpoint", i.is_feedback_2_from_mentor_past_due(), connection=connection)


class Feedback3FeedbackInstructions(FeedbackInstructions):
    """
    Send feedback #3 instructions to mentors and interns.

    When: When feedback #3 forms open, and again if feedback is missing.
          Emails may be sent with an URGENT subject if feedback is late.
          Emails may be sent multiple times if there is a internship extension.

    Templates: home/templates/home/email/feedback3-feedback-reminder.txt
               home/templates/home/email/feedback3-feedback-instructions.txt
    """
    description = 'Feedback #3 Reminder'
    slug = 'feedback3-feedback-instructions'

    @staticmethod
    def due_date(current_round):
        return current_round.feedback3_due

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_feedback3()

        for i in interns:
            email.feedback_email(i, self.request, "feedback3", i.is_feedback_3_from_mentor_past_due(), connection=connection)


class FinalFeedbackInstructions(FeedbackInstructions):
    """
    Send final feedback instructions to mentors and interns.

    When: When final feedback forms open, and again if feedback is missing.
          Emails may be sent with an URGENT subject if feedback is late.
          Emails may be sent multiple times if there is a internship extension.

    Templates: home/templates/home/email/final-feedback-reminder.txt
               home/templates/home/email/final-feedback-instructions.txt
    """
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


class CareerChatInvitation(SendEmailView):
    """
    Send an invitation to the mentors and opportunities mailing lists.
    Invite mentors and sponsor employees who are employed to work on open source
    to the careers chat and to be an informational interviewee.

    When: Week 8 - sending an invitation two weeks before the career chat in week 10.

    Template: home/templates/home/email/career-chat-invitation.txt
    """
    description = 'Invite informal chat interviewees'
    slug = 'career-chat-invitation'

    @staticmethod
    def instance(current_round):
        return current_round.week_eight_chat_text_date.date()

    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_in_good_standing_intern_selections()

        for i in interns:
            email.career_chat_invitation(current_round, self.request, template='home/email/career-chat-invitation.txt', connection=connection)


# This is a list of all reminders that staff need at different times in the
# round. Each entry should be a subclass of both RoundEvent and View.
#
# It doesn't matter what order this list is in, but I think it's less confusing
# if we keep it sorted by when in the round each event occurs.
all_round_events = (
    CFPOpen,
    CoordinatorProjectDeadline,
    MentorCheckDeadlinesReminder,
    ApplicantsDeadlinesReminder,
    ContributorsDeadlinesReminder,
    MentorApplicationDeadlinesReminder,
    MentorInternSelectionReminder,
    CoordinatorInternSelectionReminder,
    ContributorsApplicationPeriodEndedReminder,
    MentorInternSelectionDeadlineReminder,
    InternNotification,
    ContractReminder,
    InternWeek.at(week=1),
    InitialFeedbackInstructions,
    InternWeek.at(week=3),
    InternWeek.at(week=5),
    CareerChatInvitation,
    InternWeek.at(week=7),
    InternWeek.at(week=9),
    InternWeek.at(week=11),
    InternWeek.at(week=13),
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
            finalfeedback__gt=today - datetime.timedelta(days=45),
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

    pending_participations = current_round.participation_set.pending().order_by('community__name')
    approved_participations = current_round.participation_set.approved().order_by('community__name')
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
    if not current_round.internannounce.has_passed():
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
            pingnew__lte=today,
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

    mentored_communities = current_round.participation_set.approved().filter(
        project__approval_status=ApprovalStatus.APPROVED,
        project__mentorapproval__mentor=comrade,
        project__mentorapproval__approval_status=ApprovalStatus.APPROVED,
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
            if obj.is_approved() or not obj.submission_and_approval_deadline().has_passed():
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
