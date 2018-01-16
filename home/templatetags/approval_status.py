from django import template

register = template.Library()

@register.filter
def is_approver(obj, user):
    return user.is_authenticated and obj and obj.is_approver(user)

@register.filter
def is_submitter(obj, user):
    return user.is_authenticated and obj and obj.is_submitter(user)
