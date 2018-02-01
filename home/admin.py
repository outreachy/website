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
    list_display = (
            'community',
            'approval_status',
            'reason_denied',
            'round',
            )
    list_filter = (
            'approval_status',
            'participating_round',
            )
    search_fields = (
            'community__name',
            )
    inlines = (SponsorshipInline,)

    def round(self, obj):
        return obj.participating_round
    round.admin_order_field = '-participating_round__roundnumber'

class CommunityAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True

    list_display = (
            'name',
            'website',
            )
    search_fields = (
            'name',
            'website',
            )

class ProjectAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'short_title',
            'community',
            'approval_status',
            'reason_denied',
            'round',
            )
    list_filter = (
            'approval_status',
            'project_round__participating_round',
            )
    search_fields = (
            'short_title',
            'project_round__community__name',
            )

    def community(self, obj):
        return obj.project_round.community.name
    community.admin_order_field = 'project_round__community__name'

    def round(self, obj):
        return obj.project_round.participating_round
    round.admin_order_field = '-project_round__participating_round__roundnumber'

class MentorApprovalAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'mentor',
            'project_name',
            'community',
            'approval_status',
            'reason_denied',
            'round',
            )
    list_filter = (
            'approval_status',
            'project__project_round__participating_round',
            )
    search_fields = (
            'project__short_title',
            'project__project_round__community__name',
            'mentor__public_name',
            '=mentor__account__username',
            '=mentor__account__email',
            )

    def project_name(self, obj):
        return obj.project.short_title

    def community(self, obj):
        return obj.project.project_round.community.name
    community.admin_order_field = 'project__project_round__community__name'

    def round(self, obj):
        return obj.project.project_round.participating_round
    round.admin_order_field = '-project__project_round__participating_round__roundnumber'

class CoordinatorApprovalAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'coordinator',
            'community',
            'approval_status',
            'reason_denied',
            )
    list_filter = (
            'approval_status',
            )
    search_fields = (
            'community__name',
            'coordinator__public_name',
            '=coordinator__account__username',
            '=coordinator__account__email',
            )

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
            'approval_status',
            'reason_denied',
            'round',
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

    def round(self, obj):
        return obj.application_round
    round.admin_order_field = '-application_round__roundnumber'

admin.site.unregister(User)
admin.site.register(User, ComradeAdmin)

admin.site.register(ApplicantApproval, ApplicantApprovalAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(CoordinatorApproval, CoordinatorApprovalAdmin)
admin.site.register(MentorApproval, MentorApprovalAdmin)
admin.site.register(NewCommunity, CommunityAdmin)
admin.site.register(Notification)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RoundPage)
admin.site.register(Project, ProjectAdmin)
