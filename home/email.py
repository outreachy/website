from django.core.mail import send_mail
from django.template.loader import render_to_string
from email.headerregistry import Address

organizers = Address("Outreachy Organizers", "organizers", "outreachy.org")

def send_template_mail(template, context, request=None, **kwargs):
    message = render_to_string(template, context, request=request)
    kwargs.setdefault('from_email', organizers)
    send_mail(message=message.strip(), **kwargs)
