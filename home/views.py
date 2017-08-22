from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from registration.backends.simple.views import RegistrationView

# Before the form is displayed, require the mentor to create a login (LoginRequiredMixin).
# Then bring them back to this form to confirm their participation and role.
class MentorConfirmationView(LoginRequiredMixin, UpdateView):
    # We're trying to update (with UpdateView) information about the mentor
    # and store in the Django User object.
    # The User object has documentation on what fields the class has:
    # https://docs.djangoproject.com/en/1.11/ref/contrib/auth/#django.contrib.auth.models.User
    fields = ['first_name', 'last_name', 'email']
    # For pictures, we could just use gravitar with their email
    # If we need to store more info later, we need something different.

    # We need to tell Django which template to use
    # (which will contain more information about which community they're participating in)
    # so we need to update the template_name field in SingleObjectTemplateResponseMixin
    # https://docs.djangoproject.com/en/1.11/ref/class-based-views/mixins-single-object/#singleobjecttemplateresponsemixin
    template_name = "home/mentor_confirmation.html"

    # FIXME
    # On a success we want to send the mentor to their community page
    # possibly with instructions to add their project
    # But for now, just direct them back to the home page.
    success_url = "/"

    # We need to get a reference to the User object.
    # self.request.user returns the currently logged in user
    #
    # Normally the UpdateView class method get_object() will return the
    # object we're updating. Instead, we override it so it will
    # update the currently logged in User object.
    #
    # No need to specify the model class because the class of the
    # object returned by get_object() will be used.
    def get_object(self, queryset=None):
        return self.request.user

class CreateUser(RegistrationView):
    def get_success_url(self, user):
        return self.request.GET.get('next', '/')

    # The RegistrationView that django-registration provides
    # doesn't respect the next query parameter, so we have to
    # add it to the context of the template.
    def get_context_data(self, **kwargs):
        context = super(CreateUser, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next')
        return context
