# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .forms import OutreachyContactForm
from contact_form.views import ContactFormView
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

class OrganizersContactFormView(ContactFormView):
    form_class = OutreachyContactForm
    recipient_list = ['Outreachy Organizers <organizers@outreachy.org>']
    template_name = 'contact_form/contact_organizers.html'

    def get_success_url(self):
        return reverse('contacted-organizers')

class OrganizersTemplateView(TemplateView):
    template_name = 'contact_form/contacted_organizers.html'

class ApplicantHelpContactFormView(ContactFormView):
    form_class = OutreachyContactForm
    recipient_list = ['Outreachy Applicant Help <applicant-help@outreachy.org>']
    template_name = 'contact_form/contact_applicant_help.html'

    def get_success_url(self):
        return reverse('contacted-applicant-help')

class ApplicantHelpTemplateView(TemplateView):
    template_name = 'contact_form/contacted_applicant_help.html'

class ContactTemplateView(TemplateView):
    template_name = 'contact_form/contact.html'
