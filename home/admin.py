from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

import reversion.admin

from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import MentorApproval
from .models import NewCommunity
from .models import Notification
from .models import Participation
from .models import Project
from .models import RoundPage
from .models import Sponsorship

class ComradeInline(admin.StackedInline):
    model = Comrade
    can_delete = False
    verbose_name_plural = 'comrade'

class ComradeAdmin(UserAdmin):
    inlines = (ComradeInline, )

class SponsorshipInline(admin.StackedInline):
    model = Sponsorship
    can_delete = False

class ParticipationAdmin(reversion.admin.VersionAdmin):
    inlines = (SponsorshipInline,)

admin.site.unregister(User)
admin.site.register(User, ComradeAdmin)

admin.site.register(Community)
admin.site.register(CoordinatorApproval, reversion.admin.VersionAdmin)
admin.site.register(MentorApproval, reversion.admin.VersionAdmin)
admin.site.register(NewCommunity)
admin.site.register(Notification)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RoundPage)
admin.site.register(Project, reversion.admin.VersionAdmin)
