from django import forms
from django.core.exceptions import ValidationError
from django.forms import widgets
from email.headerregistry import Address


class RadioBooleanField(forms.NullBooleanField):
    """
    This is a form field for boolean-valued data where the desired UI is a
    select-style widget instead of a checkbox. Unlike the stock BooleanField,
    this means a correctly filled form absolutely must have data for this
    field. So this style of field is equivalent to NullBooleanField, but with
    the "Null" part removed: the field is always required and raises a
    validation error if the input is None.
    """
    widget = widgets.RadioSelect(choices=((True, 'Yes'), (False, 'No')))

    def __init__(self, **kwargs):
        kwargs['required'] = True
        super(RadioBooleanField, self).__init__(**kwargs)

    def validate(self, value):
        if value is None:
            raise ValidationError(self.error_messages['required'], code='required')


class InviteForm(forms.Form):
    name = forms.CharField()
    email_address = forms.EmailField()

    def get_address(self):
        return Address(self.cleaned_data['name'], addr_spec=self.cleaned_data['email_address'])

class RenameProjectSkillsForm(forms.Form):
    new_name = forms.CharField()
