import datetime
from django.core import mail
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from email.headerregistry import Address
from home.email import send_group_template_mail
from home.models import RoundPage, ApprovalStatus, get_deadline_date_for

class Command(BaseCommand):
    help = 'Sends email updates about current-round initial applications'

    def add_arguments(self, parser):
        parser.add_argument('--scheme', default='https', choices=('http', 'https'), help='Scheme for web site links.')
        parser.add_argument('--server', default='www.outreachy.org', help='Hostname for web site links.')

        parser.add_argument('message', choices=(
            'received',
            'approved',
        ), help='Select which kind of message to send.')

    def handle(self, *args, **options):
        request = {
            'scheme': options['scheme'],
            'get_host': options['server'],
        }

        now = datetime.datetime.now(datetime.timezone.utc)
        today = get_deadline_date_for(now)
        current_round = RoundPage.objects.get(
            initial_applications_close__lte=today,
            contributions_open__gt=today - datetime.timedelta(weeks=1),
        )
        current_round.today = today

        if options['message'] == 'received':
            template_name = "home/email/application-received.txt"
            applicants = current_round.applicantapproval_set.all()
        elif options['message'] == 'approved':
            template_name = "home/email/applicantapproval-approved.txt"
            applicants = current_round.applicantapproval_set.approved()

        template = get_template(template_name, using='plaintext')
        applicant_help = Address("Outreachy Applicant Helpers", "applicant-help", "outreachy.org")


        with mail.get_connection() as connection:
            for application in applicants.iterator():
                recipient = application.applicant.email_address()
                send_group_template_mail(template, {
                    'application': application,
                    'recipient': recipient,
                }, [recipient], from_email=applicant_help, request=request, connection=connection)
