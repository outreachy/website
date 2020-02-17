from django.core.management.base import LabelCommand
from django.forms import BoundField, BaseFormSet
from home import views


class Command(LabelCommand):
    help = "Export a form definition from home.views for other uses"
    args = "[form_path]"
    label = 'Python path to form'

    def handle_label(self, form_path, **options):
        obj = views
        for segment in form_path.split('.'):
            obj = getattr(obj, segment)
        self.go(obj)

    def go(self, obj, indent=0):
        if isinstance(obj, str):
            self.indented(obj, indent)

        elif isinstance(obj, BaseFormSet):
            for idx, form in enumerate(obj, 1):
                self.indented("#{}:".format(idx), indent)
                self.go(form, indent + 1)

        elif isinstance(obj, BoundField):
            if obj.is_hidden:
                return
            self.indented(obj.label, indent)
            try:
                for choice in obj.field.widget.choices:
                    self.indented(choice[1], indent + 1)
            except AttributeError:
                pass
            if obj.help_text:
                self.indented(obj.help_text, indent)
            self.stdout.write("")

        elif callable(obj):
            self.go(obj(), indent=indent)

        else:
            try:
                children = list(iter(obj))
            except TypeError:
                self.indented(repr(obj), indent)

            else:
                if len(children) > 1:
                    indent = indent + 1
                for child in children:
                    self.go(child, indent)

    def indented(self, msg, indent):
        self.stdout.write(("    " * indent) + msg)
