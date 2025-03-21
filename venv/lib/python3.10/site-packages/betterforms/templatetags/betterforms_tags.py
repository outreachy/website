from django import forms
from django import template

register = template.Library()


@register.filter(name='is_checkbox')
def is_checkbox(field):
    """
    Boolean filter for form fields to determine if a field is using a checkbox
    widget.
    """
    return isinstance(field.field.widget, forms.CheckboxInput)
