from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.db import transaction
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.test import override_settings, RequestFactory
from email.headerregistry import Address
import logging

logger = logging.getLogger(__name__)

organizers = Address("Outreachy Organizers", "organizers", "outreachy.org")
applicant_help = Address("Outreachy Applicant Helpers", "applicant-help", "outreachy.org")

def send_template_mail(template_name, context, recipient_list, request=None, **kwargs):
    # Only load the template once, no matter how many messages we're sending.
    template = get_template(template_name, using='plaintext')
    for recipient in recipient_list:
        # Templates used with this function expect the 'recipient' context
        # variable to contain a single address, not a list, so override
        # send_group_template_mail's default.
        context['recipient'] = recipient
        send_group_template_mail(template, context, [recipient], request, **kwargs)

def send_group_template_mail(template, context, recipient_list, request=None, **kwargs):
    # Load the specified template name unless it's already a Template object.
    if not hasattr(template, 'render'):
        template = get_template(template, using='plaintext')

    context.setdefault('recipient', recipient_list)
    message = template.render(context, request).strip()
    subject, body = message.split('\n', 1)
    kwargs.setdefault('from_email', organizers)
    send_mail(message=body.strip(), subject=subject.strip(), recipient_list=recipient_list, **kwargs)

def approval_status_changed(obj, request, **kwargs):
    get_recipients = {
        obj.PENDING: obj.get_approver_email_list,
        obj.WITHDRAWN: obj.get_approver_email_list,
        obj.APPROVED: obj.get_submitter_email_list,
        obj.REJECTED: obj.get_submitter_email_list,
    }[obj.approval_status]

    # produces template names like "home/email/project-pending.txt"
    template = "{}/email/{}-{}.txt".format(
            obj._meta.app_label,
            obj._meta.model_name,
            obj.get_approval_status_display().lower())

    try:
        send_template_mail(template, {
                obj._meta.model_name: obj,
            },
            request=request,
            recipient_list=get_recipients(),
            **kwargs)
    except TemplateDoesNotExist:
        logger.info(
            "not sending approval status change email because %s does not exist",
            template, exc_info=True)

def notify_mentor(participation, notification, request):
    send_template_mail('home/email/notify-mentors.txt', {
        'notification': notification,
        'participation': participation,
        },
        request=request,
        recipient_list=[notification.comrade.email_address()])

def project_nonfree_warning(project, request):
    send_template_mail('home/email/project-warning.txt', {
        'project': project,
        },
        request=request,
        recipient_list=[organizers])

def project_applicant_review(project, request, **kwargs):
    send_group_template_mail('home/email/mentor-applicant-updates.txt', {
        'project': project,
        },
        request=request,
        recipient_list=project.get_mentor_email_list(),
        **kwargs)

def mentor_application_deadline_reminder(project, request, **kwargs):
    send_group_template_mail('home/email/mentor-application-deadline-approaching.txt', {
        'project': project,
        },
        request=request,
        recipient_list=project.get_mentor_email_list(),
        **kwargs)

def mentor_intern_selection_reminder(project, request, **kwargs):
    send_group_template_mail('home/email/mentor-choose-intern.txt', {
        'project': project,
        },
        request=request,
        recipient_list=project.get_mentor_email_list(),
        **kwargs)

def coordinator_intern_selection_reminder(participation, request, **kwargs):
    email_list = participation.get_submitter_email_list()
    if email_list:
        send_group_template_mail('home/email/coordinator-intern-selection.txt', {
            'current_round': participation.participating_round,
            'community': participation.community,
            },
            request=request,
            recipient_list=email_list,
            **kwargs)

def co_mentor_intern_selection_notification(intern_selection, request):
    mentor_email = intern_selection.mentors.get().mentor.account.email
    email_list = []
    for email in intern_selection.project.get_mentor_email_list():
        if email.addr_spec == mentor_email:
            continue
        email_list.append(email)

    if email_list:
        send_group_template_mail('home/email/co-mentor-sign-agreement.txt', {
            'intern_selection': intern_selection,
            },
            request=request,
            recipient_list=email_list)

def intern_selection_conflict_notification(intern_selection, request):
    conflicts = intern_selection.get_intern_selection_conflicts()
    if not conflicts:
        return

    email_list = []
    for conflict in conflicts:
        email_list.extend(conflict.project.get_mentor_email_list())
        email_list.extend(conflict.project.get_approver_email_list())
    email_list.extend([organizers])

    if email_list:
        send_group_template_mail('home/email/intern-selection-conflict.txt', {
            'intern_selection': intern_selection,
            },
            request=request,
            recipient_list=email_list)

def applicant_deadline_reminder(late_projects, promoted_projects, closed_projects, current_round, request, **kwargs):
    send_group_template_mail('home/email/applicants-deadline-reminder.txt', {
        'late_projects': late_projects,
        'closed_projects': closed_projects,
        'promoted_projects': promoted_projects,
        'current_round': current_round,
        },
        request=request,
        recipient_list=['announce@lists.outreachy.org'],
        **kwargs)

def applicant_essay_needs_updated(applicant, request):
    send_template_mail('home/email/applicant-essay-needs-updated.txt', {
        'comrade': applicant,
        },
        request=request,
        from_email=applicant_help,
        recipient_list=[applicant.email_address()])

def applicant_school_info_needs_updated(applicant, request):
    send_template_mail('home/email/applicant-school-info-needs-updated.txt', {
        'comrade': applicant,
        },
        request=request,
        from_email=applicant_help,
        recipient_list=[applicant.email_address()])

def contributor_deadline_reminder(contributor, current_round, request, **kwargs):
    from .models import Role # oops, circular import dependency :-(
    send_template_mail('home/email/contributors-deadline-reminder.txt', {
        'current_round': current_round,
        'role': Role(contributor.account, current_round),
        'timezone': contributor.timezone,
        'comrade': contributor,
        },
        request=request,
        recipient_list=[contributor.email_address()],
        **kwargs)

def contributor_application_period_ended(contributor, current_round, request, **kwargs):
    from .models import Role # oops, circular import dependency :-(
    send_template_mail('home/email/contributors_application_period_ended.txt', {
        'current_round': current_round,
        'role': Role(contributor.account, current_round),
        'timezone': contributor.timezone,
        'comrade': contributor,
        },
        request=request,
        recipient_list=[contributor.email_address()],
        **kwargs)

def notify_accepted_intern(intern_selection, request, **kwargs):
    emails = [intern_selection.applicant.applicant.email_address()]
    for m in intern_selection.mentors.all():
        emails.append(m.mentor.email_address())
    emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
    send_group_template_mail('home/email/interns-notify.txt', {
        'intern_selection': intern_selection,
        'coordinator_names': intern_selection.project.project_round.community.get_coordinator_names(),
        'current_round': intern_selection.project.project_round.participating_round,
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def biweekly_internship_email(intern_selection, request, template, **kwargs):
    emails = [intern_selection.applicant.applicant.email_address()]
    for m in intern_selection.mentors.all():
        emails.append(m.mentor.email_address())
    emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
    send_group_template_mail(template, {
        'intern_selection': intern_selection,
        'project': intern_selection.project,
        'community': intern_selection.project.project_round.community,
        'current_round': intern_selection.project.project_round.participating_round,
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def feedback_email(intern_selection, request, stage, past_due, **kwargs):
    emails = []
    if past_due:
        emails.append(organizers)
        for m in intern_selection.mentors.all():
            emails.append(m.mentor.email_address())
        emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
        template = 'home/email/' + stage + '-feedback-reminder.txt'
    else:
        emails.append(intern_selection.applicant.applicant.email_address())
        for m in intern_selection.mentors.all():
            emails.append(m.mentor.email_address())
        emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
        template = 'home/email/' + stage + '-feedback-instructions.txt'
    send_group_template_mail(template, {
        'intern_selection': intern_selection,
        'current_round': intern_selection.project.project_round.participating_round,
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def notify_survey(survey_tracker, request):
    if survey_tracker.intern_info:
        name = survey_tracker.intern_info.applicant.applicant.public_name
        email = survey_tracker.intern_info.applicant.applicant.email_address()
        community = survey_tracker.intern_info.project.project_round.community.name
        internstarts = survey_tracker.intern_info.project.project_round.participating_round.internstarts
        internends = survey_tracker.intern_info.project.project_round.participating_round.internends
    elif survey_tracker.alumni_info:
        name = survey_tracker.alumni_info.name
        email = Address(name, addr_spec=survey_tracker.alumni_info.email)
        community = survey_tracker.alumni_info.community
        internstarts = survey_tracker.alumni_info.page.round_start
        internends = survey_tracker.alumni_info.page.round_end
    else:
        return
    signer = TimestampSigner()
    token = signer.sign(survey_tracker.pk)

    send_group_template_mail('home/email/alum_survey.txt', {
        'name': name,
        'email': email,
        'community': community,
        'internstarts': internstarts,
        'internends': internends,
        'token': token,
        },
        request=request,
        recipient_list=[email])


@override_settings(ALLOWED_HOSTS=['www.outreachy.org'], EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
# Run in a transaction so none of the sample objects are saved
@transaction.atomic
def message_samples():
    """
    This function is meant for testing: It fakes sending every type of
    email using randomly-generated objects. Run it using this command:

    ./manage.py shell -c 'import home.email; home.email.message_samples()'
    """

    from . import factories

    logging.basicConfig(level=logging.INFO)

    request = RequestFactory().get('/', secure=True, HTTP_HOST='www.outreachy.org')

    intern_selection = factories.InternSelectionFactory(active=True)
    mentorapproval = intern_selection.mentors.get()
    project = mentorapproval.project
    # add a co-mentor who hasn't signed the contract
    factories.MentorApprovalFactory(project=project, approval_status='A')
    participation = project.project_round
    current_round = participation.participating_round
    community = participation.community
    coordinatorapproval = factories.CoordinatorApprovalFactory(community=community)
    applicantapproval = intern_selection.applicant
    applicant = applicantapproval.applicant
    factories.ContributionFactory(round=current_round, applicant=applicantapproval, project=project)
    contributor = applicant

    objects = (
        (coordinatorapproval, {}),
        (participation, {}),
        (project, {}),
        (mentorapproval, {}),
        (applicantapproval, {'from_email': applicant_help}),
    )

    for obj, kwargs in objects:
        for status, label in obj.APPROVAL_STATUS_CHOICES:
            obj.approval_status = status
            obj.save()
            approval_status_changed(obj, request, **kwargs)

    # For further examples, let's say everything's approved.
    for obj, kwargs in objects:
        obj.approval_status = obj.APPROVED
        obj.save()

    notification = factories.NotificationFactory(community=community)
    notify_mentor(participation, notification, request)

    project_nonfree_warning(project, request)
    project_applicant_review(project, request)
    mentor_application_deadline_reminder(project, request)
    mentor_intern_selection_reminder(project, request)
    coordinator_intern_selection_reminder(participation, request)
    co_mentor_intern_selection_notification(intern_selection, request)
    intern_selection_conflict_notification(intern_selection, request)
    # TODO: applicant_deadline_reminder
    applicant_essay_needs_updated(applicant, request)
    applicant_school_info_needs_updated(applicant, request)
    contributor_deadline_reminder(contributor, current_round, request)
    contributor_application_period_ended(contributor, current_round, request)
    notify_accepted_intern(intern_selection, request)
    for week in ('one', 'three', 'five'):
        template = 'home/email/internship-week-{}.txt'.format(week)
        biweekly_internship_email(intern_selection, request, template)
    initial_feedback_email(intern_selection, request)
    # TODO: notify_survey

    # An easy way to abort the current transaction
    raise SystemExit(0)
