from .views import OrganizersContactFormView, OrganizersTemplateView, ApplicantHelpContactFormView, ApplicantHelpTemplateView, ContactTemplateView
from django.urls import re_path

urlpatterns = [
    re_path(r'^organizers/$', OrganizersContactFormView.as_view(), name='contact-organizers'),
    re_path(r'^organizers/sent/$', OrganizersTemplateView.as_view(), name='contacted-organizers'),
    re_path(r'^applicant-help/$', ApplicantHelpContactFormView.as_view(), name='contact-applicant-help'),
    re_path(r'^applicant-help/sent/$', ApplicantHelpTemplateView.as_view(), name='contacted-applicant-help'),
    re_path(r'^contact-us/$', ContactTemplateView.as_view(), name='contact-us'),
]
