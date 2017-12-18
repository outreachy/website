from registration.backends.simple.views import RegistrationView

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
