from django.core.management.base import LabelCommand
from django.template import TemplateDoesNotExist, loader
import re

def show_includes(template_path, seen, depth=0):
    if template_path in seen:
        return
    print("  " * depth + template_path)
    seen.add(template_path)

    try:
        template = loader.get_template(template_path).template
    except TemplateDoesNotExist:
        print("  " * depth + "*** previous template not found!")
        return

    for included in re.findall(r"{%\s*include\s+([^\s]*)[^%]*%}", template.source):
        if included[0] in "\"'":
            show_includes(included[1:-1], seen, depth + 1)
        else:
            print("  " * (depth + 1) + "*** template name given by expression:", repr(included))

class Command(LabelCommand):
    help = "Reports which templates are included from the given roots, recursively"
    args = "[template_path]"
    label = 'template path'

    def handle_label(self, template_path, **options):
        show_includes(template_path, set())
