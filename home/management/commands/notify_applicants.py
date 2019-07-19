import datetime
from django.core import mail
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from home.email import send_group_template_mail
from home.models import RoundPage, get_deadline_date_for


class Command(BaseCommand):
    help = 'Sends email updates about current-round initial applications'

    def handle(self, *args, **options):
        template = get_template("home/email/applicantapproval-approved.txt", using='plaintext')

        now = datetime.datetime.now(datetime.timezone.utc)
        today = get_deadline_date_for(now)
        current_round = RoundPage.objects.get(
            initial_applications_close__lte=today,
            contributions_open__gt=today - datetime.timedelta(weeks=1),
        )
        current_round.today = today

        with mail.get_connection() as connection:
            for application in current_round.applicantapproval_set.approved().iterator():
                recipient = application.applicant.email_address()
                send_group_template_mail(template, {
                    'application': application,
                    'recipient': recipient,
                }, [recipient], connection=connection)
