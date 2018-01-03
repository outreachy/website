from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from registration.forms import RegistrationForm

from .models import Comrade

User = get_user_model()

class ComradeRegister(RegistrationForm):
    email = forms.EmailField(label="Email (internal)",
            help_text="Your email. This will be used to reset your password and send you Outreachy program announcements. Applicant emails will be shared with organizers, coordinators, mentors, and volunteers. Coordinator and mentor emails will be shared with applicants.",
            required=True)

    class Meta(UserCreationForm.Meta):
        model = Comrade
        fields = [
                User.USERNAME_FIELD,
                'email',
                'password1',
                'password2',
                'public_name',
                'nick_name',
                'legal_name',
                'pronouns',
                'pronouns_to_participants',
                'pronouns_public',
                'timezone',
                'primary_language',
                'second_language',
                'third_language',
                'fourth_language',
                ]
