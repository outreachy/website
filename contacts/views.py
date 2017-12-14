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

class MentorsContactFormView(ContactFormView):
    form_class = OutreachyContactForm
    recipient_list = ['Outreachy mentors <mentors@lists.outreachy.org>']
    template_name = 'contact_form/contact_mentors.html'

    def get_success_url(self):
        return reverse('contacted-mentors')

class MentorsTemplateView(TemplateView):
    template_name = 'contact_form/contacted_mentors.html'
