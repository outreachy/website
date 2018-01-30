from django.views.generic import TemplateView

class ServerErrorView(TemplateView):
    template_name = '500.html'
    template_engine = 'errorsafe' # from settings.TEMPLATES

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['status'] = 500
        return super(ServerErrorView, self).render_to_response(context, **response_kwargs)
