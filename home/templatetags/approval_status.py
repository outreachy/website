from django import template

register = template.Library()

@register.filter
def is_approver(obj, user):
    return obj.is_approver(user)

@register.filter
def is_submitter(obj, user):
    return obj.is_submitter(user)
