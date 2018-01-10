from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import Participation
from .models import RoundPage
from .models import Project

class ComradeInline(admin.StackedInline):
    model = Comrade
    can_delete = False
    verbose_name_plural = 'comrade'

class ComradeAdmin(UserAdmin):
    inlines = (ComradeInline, )

admin.site.unregister(User)
admin.site.register(User, ComradeAdmin)

admin.site.register(Community)
admin.site.register(CoordinatorApproval)
admin.site.register(MentorApproval)
admin.site.register(Participation)
admin.site.register(RoundPage)
admin.site.register(Project)
