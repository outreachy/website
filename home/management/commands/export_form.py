from django.core.management.base import LabelCommand
from django.forms import BaseForm, BaseFormSet
from home import views


class Command(LabelCommand):
    help = "Export a form definition from home.views as HTML"
    args = "[form_path]"
    label = 'Python path to form'

    def handle_label(self, form_path, **options):
        obj = views
        for segment in form_path.split('.'):
            obj = getattr(obj, segment)
        self.go(obj)

    def go(self, obj):
        if isinstance(obj, str):
            self.stdout.write('<h1>{}</h1>'.format(obj))

        elif isinstance(obj, BaseFormSet):
            self.stdout.write('<ol>')
            for idx, form in enumerate(obj, 1):
                self.stdout.write('<li>')
                self.stdout.write(form.as_p())
                self.stdout.write('</li>')
            self.stdout.write('</ol>')

        elif isinstance(obj, BaseForm):
            self.stdout.write(obj.as_p())

        elif callable(obj):
            self.go(obj())

        else:
            try:
                children = iter(obj)
            except TypeError:
                self.stdout.write("<p><code>{!r}</code></p>".format(obj))

            else:
                for child in children:
                    self.go(child)
