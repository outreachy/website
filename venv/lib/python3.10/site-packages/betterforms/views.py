from django.views.generic import ListView, FormView


class BrowseView(ListView, FormView):
    """
    Class Based view for working with changelists.
    """
    def post(self, *args, **kwargs):
        return self.http_method_not_allowed(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = {
            'initial': self.get_initial(),
            'queryset': self.object_list,
            'data': self.request.GET,
            'files': self.request.FILES,
        }
        return kwargs

    def get_context_data(self, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        kwargs['form'] = form
        if form.is_valid():
            kwargs['object_list'] = form.get_queryset()
        else:
            kwargs['object_list'] = form.base_queryset.none()
        kwargs = super().get_context_data(**kwargs)
        return kwargs
