from django import forms
from django.forms import widgets


class RadioBooleanField(forms.BooleanField):
    widget = widgets.RadioSelect(choices=((True, 'Yes'), (False, 'No')))

    def __init__(self, **kwargs):
        kwargs['required'] = True
        super(RadioBooleanField, self).__init__(**kwargs)

    def validate(self, value):
        if value is None:
            raise ValidationError(self.error_messages['required'], code='required')
