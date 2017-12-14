"""
A contact form for allowing users to send email messages through
a web interface. The user specifies their name and email to be used
in the From header, and the topic field will be used to generate the
Subject header.

"""
from __future__ import unicode_literals

from contact_form.forms import ContactForm
from django import forms

class OutreachyContactForm(ContactForm):

    topic = forms.CharField(max_length=100,
            label='Subject')

    body = forms.CharField(widget=forms.Textarea,
                           label='Message')

    field_order = ['name', 'email', 'topic', 'body']

    def from_email(self):
        # This Python coding style of ** expands the dictionary to be passed as named arguments
        return '"{name}" <{email}>'.format(**self.cleaned_data)

    def subject(self):
        return self.cleaned_data['topic']

    def message(self):
        return self.cleaned_data['body']
