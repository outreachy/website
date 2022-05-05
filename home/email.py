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
mentors_mailing_list = Address("Outreachy mentors list", "mentors", "lists.outreachy.org")

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

def cfp_open(current_round, request, **kwargs):
    send_template_mail('home/email/cfp-open.txt', {
        'current_round': current_round,
        },
        request=request,
        recipient_list=[mentors_mailing_list],
        **kwargs,
        )

def coordinator_project_deadline(current_round, participation, request, **kwargs):
    email_list = participation.community.get_coordinator_email_list()
    email_list.append(organizers)
    email_list.append(applicant_help)
    send_group_template_mail('home/email/coordinator-project-deadline.txt', {
        'current_round': current_round,
        'participation': participation,
        'community': participation.community,
        },
        request=request,
        recipient_list=email_list,
        **kwargs,
        )

def notify_mentor(participation, notification, request):
    send_template_mail('home/email/notify-mentors.txt', {
        'notification': notification,
        'participation': participation,
        },
        request=request,
        recipient_list=[notification.comrade.email_address()])

def notify_organizers_of_new_community(new_community):
    send_template_mail(
        'home/email/new-community-created.txt',
        {
            'new_community': new_community
        },
        recipient_list=[organizers]
    )

def project_nonfree_warning(project, request):
    send_template_mail('home/email/project-warning.txt', {
        'project': project,
        },
        request=request,
        recipient_list=[organizers])

def invite_mentor(project, recipient, request):
    # Calling these functions from the shell is tedious enough without having
    # to construct a real Request object. If the `user` field is missing, just
    # use a default address.
    if hasattr(request, 'user'):
        sender = request.user.comrade.email_address
    else:
        sender = organizers

    # We could set from_email=sender, but "forging" email makes it look more
    # like spam, so just use our own address and include the sender in the
    # message body instead.
    send_template_mail(
        'home/email/invite-mentor.txt',
        {
            'project': project,
            'recipient': recipient,
            'sender': sender,
        },
        request=request,
        recipient_list=[recipient],
    )

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

def coordinator_intern_selection_reminder(participation, request, **kwargs):
    email_list = participation.community.get_coordinator_email_list()
    if email_list:
        send_group_template_mail('home/email/coordinator-intern-selection.txt', {
            'current_round': participation.participating_round,
            'community': participation.community,
            },
            request=request,
            recipient_list=email_list,
            **kwargs)

def mentor_intern_selection_deadline_reminder(project, request, **kwargs):
    email_list = project.get_mentor_email_list()
    # Include community coordinators (who approve projects to participate)
    email_list.extend(project.get_approver_email_list())
    # Include Outreachy organizers
    email_list.extend([organizers])

    send_group_template_mail('home/email/mentor-intern-selection-deadline-reminder.txt', {
        'project': project,
        },
        request=request,
        recipient_list=email_list,
        **kwargs)

def co_mentor_intern_selection_notification(intern_selection, email_list, request):
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

def applicant_deadline_reminder(closed_projects, current_round, request, **kwargs):
    send_group_template_mail('home/email/applicants-deadline-reminder.txt', {
        'closed_projects': closed_projects,
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
        # only use information available to the subject, not to request.user
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
        # only use information available to the subject, not to request.user
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
        'current_round': intern_selection.project.round(),
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def reminder_sign_internship_agreement(intern_selection, request, **kwargs):
    emails = [intern_selection.applicant.applicant.email_address()]
    emails.append(organizers)
    send_group_template_mail('home/email/reminder-sign-internship-agreement.txt', {
        'intern_selection': intern_selection,
        'current_round': intern_selection.project.round(),
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
        'current_round': intern_selection.project.round(),
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
        'current_round': intern_selection.project.round(),
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def career_chat_invitation(current_round, request, template, **kwargs):
    emails = ['opportunities@lists.outreachy.org', 'mentors@lists.outreachy.org']
    send_group_template_mail(template, {
        'current_round': current_round,
        },
        request=request,
        recipient_list=emails,
        **kwargs)

def notify_survey(survey_tracker, request):
    if survey_tracker.intern_info:
        name = survey_tracker.intern_info.applicant.applicant.public_name
        email = survey_tracker.intern_info.applicant.applicant.email_address()
        community = survey_tracker.intern_info.project.project_round.community.name
        internstarts = survey_tracker.intern_info.project.round().internstarts
        internends = survey_tracker.intern_info.project.round().internends
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
