from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.test import override_settings, RequestFactory
from email.headerregistry import Address

organizers = Address("Outreachy Organizers", "organizers", "outreachy.org")

def send_template_mail(template, context, recipient_list, request=None, **kwargs):
    for recipient in recipient_list:
        context['recipient'] = recipient
        message = render_to_string(template, context, request=request, using='plaintext').strip()
        subject, body = message.split('\n', 1)
        kwargs.setdefault('from_email', organizers)
        send_mail(message=body.strip(), subject=subject.strip(), recipient_list=[recipient], **kwargs)

def participation_pending(participation, request):
    send_template_mail('home/email/community-signup.txt', {
        'participation': participation,
        },
        request=request,
        recipient_list=[organizers])

def participation_approved(participation, request):
    send_template_mail('home/email/community-approved.txt', {
        'participation': participation,
        },
        request=request,
        recipient_list=participation.community.get_coordinator_email_list())

def notify_mentor(participation, notification, request):
    send_template_mail('home/email/notify-mentors.txt', {
        'notification': notification,
        'participation': participation,
        },
        request=request,
        recipient_list=[notification.comrade.email_address()])

def project_pending(project, request):
    send_template_mail('home/email/project-review.txt', {
        'project': project,
        },
        request=request,
        recipient_list=project.project_round.community.get_coordinator_email_list())

def project_nonfree_warning(project, request):
    send_template_mail('home/email/project-warning.txt', {
        'project': project,
        },
        request=request,
        recipient_list=[organizers])

def project_approved(project, request):
    send_template_mail('home/email/project-approved.txt', {
        'project': project,
        },
        request=request,
        recipient_list=project.get_mentor_email_list())

def mentorapproval_pending(mentorapproval, request):
    send_template_mail('home/email/mentor-review.txt', {
        'mentorapproval': mentorapproval,
        },
        request=request,
        recipient_list=mentorapproval.project.project_round.community.get_coordinator_email_list())

def coordinatorapproval_pending(coordinatorapproval, request):
    send_template_mail('home/email/coordinator-review.txt', {
        'coordinatorapproval': coordinatorapproval,
        },
        request=request,
        recipient_list=coordinatorapproval.community.get_coordinator_email_list() + [organizers])

def coordinatorapproval_approved(coordinatorapproval, request):
    send_template_mail('home/email/coordinator-approved.txt', {
        'coordinatorapproval': coordinatorapproval,
        },
        request=request,
        recipient_list=[coordinatorapproval.coordinator.email_address()])

def mentorapproval_approved(mentorapproval, request):
    send_template_mail('home/email/mentor-approved.txt', {
        'mentorapproval': mentorapproval,
        },
        request=request,
        recipient_list=[mentorapproval.mentor.email_address()])

def mentor_list_subscribe(mentor, request):
    # Subscribe the mentor to the mentor mailing list
    # We need to spoof sending email from the email address we want to subscribe,
    # since using 'subscribe address=email' in the body doesn't work.
    # This is still a pain because organizers need to approve subscription requests.
    # We really need mailman 3.
    send_template_mail('home/email/mentor-list-subscribe.txt', {
        'comrade': mentor,
        },
        request=request,
        from_email=Address(
            "{name} via {domain} mentor approval".format(
                name=mentor.public_name,
                domain=request.get_host()),
            addr_spec=mentor.account.email
            ),
        recipient_list=[Address('', 'mentors-join', 'lists.outreachy.org')])

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
    coordinatorapproval_pending(coordinatorapproval, request)
    coordinatorapproval_approved(coordinatorapproval, request)

    participation = models.Participation.objects.all()[0]
    participation_pending(participation, request)
    participation_approved(participation, request)

    notification = models.Notification.objects.all()[0]
    notify_mentor(participation, notification, request)

    project = models.Project.objects.all()[0]
    project_pending(project, request)
    project_nonfree_warning(project, request)
    project_approved(project, request)

    mentorapproval = models.MentorApproval.objects.all()[0]
    mentorapproval_pending(mentorapproval, request)
    mentorapproval_approved(mentorapproval, request)

    comrade = models.Comrade.objects.all()[0]
    mentor_list_subscribe(comrade, request)
