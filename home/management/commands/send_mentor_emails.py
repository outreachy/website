from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from home.models import Project  # Import the Project model from home app

class Command(BaseCommand):
    help = "Send emails to mentors asking for promising applicants"

    def handle(self, *args, **kwargs):
        current_date = timezone.now()

        # Retrieve the project you're working with (you can change this to dynamically fetch projects)
        project = Project.objects.get(id=1)  # Filter by the specific project or modify the query

        # Get mentor emails using the method from your model
        mentor_emails = project.get_mentor_email_list()

        for email in mentor_emails:
            subject = "Outreachy: Do you have any promising applicants?"
            message = (
                f"Dear Mentor,\n\n"
                "We're reaching out to ask if you have received any promising applicants for your project. "
                "If so, please let us know so we can verify their eligibility and ensure they proceed smoothly.\n\n"
                "If you haven't received promising applicants, let us know! We can help promote your project to attract applicants.\n\n"
                "Kind regards,\nOutreachy Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Email sent to {email}"))

        self.stdout.write(self.style.SUCCESS("All mentor emails have been sent!"))
