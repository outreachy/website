from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.template.loader import render_to_string
from django.test import override_settings, RequestFactory
from email.headerregistry import Address

organizers = Address("Outreachy Organizers", "organizers", "outreachy.org")
applicant_help = Address("Outreachy Applicant Helpers", "applicant-help", "outreachy.org")

def send_template_mail(template, context, recipient_list, request=None, **kwargs):
    for recipient in recipient_list:
        context['recipient'] = recipient
        message = render_to_string(template, context, request=request, using='plaintext').strip()
        subject, body = message.split('\n', 1)
        if 'initial application' in subject:
            kwargs.setdefault('from_email', applicant_help)
        else:
            kwargs.setdefault('from_email', organizers)
        send_mail(message=body.strip(), subject=subject.strip(), recipient_list=[recipient], **kwargs)

def send_group_template_mail(template, context, recipient_list, request=None, **kwargs):
    context['recipient'] = recipient_list
    message = render_to_string(template, context, request=request, using='plaintext').strip()
    subject, body = message.split('\n', 1)
    kwargs.setdefault('from_email', organizers)
    send_mail(message=body.strip(), subject=subject.strip(), recipient_list=recipient_list, **kwargs)

def applicant_approval_status_changed(obj, request):
    if obj.approval_status == obj.PENDING:
        recipients = obj.get_approver_email_list()
    elif obj.approval_status == obj.APPROVED:
        recipients = obj.get_submitter_email_list()
    elif obj.approval_status == obj.REJECTED:
        recipients = obj.get_submitter_email_list()
    else:
        # FIXME: write emails for other states
        return

    # produces template names like "home/email/project-pending.txt"
    template = "{}/email/{}-{}.txt".format(
            obj._meta.app_label,
            obj._meta.model_name,
            obj.get_approval_status_display().lower())
    context = { obj._meta.model_name: obj }
    send_template_mail(template, context, request=request, recipient_list=recipients)

def approval_status_changed(obj, request):
    if obj.approval_status == obj.PENDING:
        recipients = obj.get_approver_email_list()
    elif obj.approval_status == obj.APPROVED:
        recipients = obj.get_submitter_email_list()
    else:
        # FIXME: write emails for other states
        return

    # produces template names like "home/email/project-pending.txt"
    template = "{}/email/{}-{}.txt".format(
            obj._meta.app_label,
            obj._meta.model_name,
            obj.get_approval_status_display().lower())
    context = { obj._meta.model_name: obj }
    send_template_mail(template, context, request=request, recipient_list=recipients)

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
        recipient_list=[applicant.email_address()])

def applicant_school_info_needs_updated(applicant, request):
    send_template_mail('home/email/applicant-school-info-needs-updated.txt', {
        'comrade': applicant,
        },
        request=request,
        recipient_list=[applicant.email_address()])

def contributor_deadline_reminder(contributor, current_round, request, **kwargs):
    upcoming_deadlines, passed_deadlines = contributor.get_projects_with_upcoming_and_passed_deadlines()
    send_template_mail('home/email/contributors-deadline-reminder.txt', {
        'current_round': current_round,
        'upcoming_deadlines': upcoming_deadlines,
        'passed_deadlines': passed_deadlines,
        'timezone': contributor.timezone,
        'comrade': contributor,
        },
        request=request,
        recipient_list=[contributor.email_address()],
        **kwargs)

def contributor_application_period_ended(contributor, current_round, request, **kwargs):
    passed_deadlines = contributor.get_passed_projects_not_applied_to()
    send_template_mail('home/email/contributors_application_period_ended.txt', {
        'current_round': current_round,
        'passed_deadlines': passed_deadlines,
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

def week_one_email(intern_selection, request, **kwargs):
    emails = [intern_selection.applicant.applicant.email_address()]
    for m in intern_selection.mentors.all():
        emails.append(m.mentor.email_address())
    emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
    send_group_template_mail('home/email/internship-week-one.txt', {
        'intern_selection': intern_selection,
        'current_round': intern_selection.project.project_round.participating_round,
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def initial_feedback_email(intern_selection, request, **kwargs):
    emails = [intern_selection.applicant.applicant.email_address()]
    for m in intern_selection.mentors.all():
        emails.append(m.mentor.email_address())
    emails = emails + intern_selection.project.project_round.community.get_coordinator_email_list()
    send_group_template_mail('home/email/initial-feedback-instructions.txt', {
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
def message_samples():
    """
    This function is meant for testing: It fakes sending every type of
    email using an arbitary object from your current database, so make
    sure you have created some test data first. Run it using this
    command:

    ./manage.py shell -c 'import home.email; home.email.message_samples()'
    """

    from . import models
    request = RequestFactory().get('/', HTTP_HOST='www.outreachy.org')

    coordinatorapproval = models.CoordinatorApproval.objects.all()[0]
    participation = models.Participation.objects.all()[0]
    project = models.Project.objects.all()[0]
    mentorapproval = models.MentorApproval.objects.all()[0]

    objects = (
            coordinatorapproval,
            participation,
            project,
            mentorapproval,
            )

    for obj in objects:
        for status, label in models.ApprovalStatus.APPROVAL_STATUS_CHOICES:
            obj.approval_status = status
            approval_status_changed(obj, request)

    project_nonfree_warning(project, request)

    notification = models.Notification.objects.all()[0]
    notify_mentor(participation, notification, request)
