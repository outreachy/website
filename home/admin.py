from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

import reversion.admin

from .models import ApplicantApproval
from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import EmploymentTimeCommitment
from .models import MentorApproval
from .models import NewCommunity
from .models import Notification
from .models import Participation
from .models import Project
from .models import RoundPage
from .models import SchoolTimeCommitment
from .models import Sponsorship
from .models import TimeCommitment

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

class CommunityAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True

class SchoolTimeCommitmentsInline(admin.StackedInline):
    model = SchoolTimeCommitment
    can_delete = False
    verbose_name_plural = 'School term'

class EmploymentTimeCommitmentsInline(admin.StackedInline):
    model = EmploymentTimeCommitment
    can_delete = False
    verbose_name_plural = 'Employment period'

class TimeCommitmentsInline(admin.StackedInline):
    model = TimeCommitment
    can_delete = False
    verbose_name_plural = 'Time commitment'

class ApplicantApprovalAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'applicant',
            'get_approval_status_display',
            'reason_denied',
            'application_round',
            )
    list_filter = (
            'approval_status',
            'application_round',
            )
    search_fields = (
            'applicant__public_name',
            '=applicant__account__username',
            '=applicant__account__email',
            )
    inlines = (SchoolTimeCommitmentsInline, EmploymentTimeCommitmentsInline, TimeCommitmentsInline)

admin.site.unregister(User)
admin.site.register(User, ComradeAdmin)

admin.site.register(ApplicantApproval, ApplicantApprovalAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(CoordinatorApproval, reversion.admin.VersionAdmin)
admin.site.register(MentorApproval, reversion.admin.VersionAdmin)
admin.site.register(NewCommunity)
admin.site.register(Notification)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RoundPage)
admin.site.register(Project, reversion.admin.VersionAdmin)
