from django.core.mail import send_mail
from django.template.loader import render_to_string
from email.headerregistry import Address

organizers = Address("Outreachy Organizers", "organizers", "outreachy.org")

def send_template_mail(template, context, request=None, **kwargs):
    message = render_to_string(template, context, request=request)
    kwargs.setdefault('from_email', organizers)
    send_mail(message=message.strip(), **kwargs)

def participation_pending(participation, request):
    send_template_mail('home/email/community-signup.txt', {
        'community': participation.community,
        'current_round': participation.participating_round,
        'participation_info': participation,
        },
        request=request,
        subject='Approve community participation - {name}'.format(name=participation.community.name),
        recipient_list=[organizers])

def notify_mentor(participation, notification, request):
    send_template_mail('home/email/notify-mentors.txt', {
        'community': participation.community,
        'notification': notification,
        'current_round': participation.participating_round,
        },
        request=request,
        subject='Mentor for {name} in Outreachy'.format(name=participation.community.name),
        recipient_list=[notification.comrade.email_address()])

def project_pending(project, request):
    community = project.project_round.community
    send_template_mail('home/email/project-review.txt', {
        'community': community,
        'project': project,
        },
        request=request,
        subject='Approve Outreachy intern project proposal for {name}'.format(name=community.name),
        recipient_list=community.get_coordinator_email_list())

def project_nonfree_warning(project, request):
    community = project.project_round.community
    send_template_mail('home/email/project-warning.txt', {
        'community': community,
        'project': project,
        },
        request=request,
        subject='Approve Outreachy intern project proposal for {name}'.format(name=community.name),
        recipient_list=[organizers])

def mentorapproval_pending(mentorapproval, request):
    community = mentorapproval.project.project_round.community
    send_template_mail('home/email/mentor-review.txt', {
        'project': mentorapproval.project,
        'community': community,
        'mentorapproval': mentorapproval,
        },
        request=request,
        subject='Approve Outreachy mentor for {name}'.format(name=community.name),
        recipient_list=community.get_coordinator_email_list())

def mentorapproval_approved(mentorapproval, request):
    community = mentorapproval.project.project_round.community
    send_template_mail('home/email/mentor-approved.txt', {
        'community': community,
        'project': mentorapproval.project,
        },
        request=request,
        subject='Approved as Outreachy mentor for {name}'.format(name=community.name),
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
        subject='Subscribe {name}'.format(name=mentor.public_name),
        recipient_list=['mentors-join@lists.outreachy.org'])
