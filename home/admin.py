from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse

import reversion.admin

from .models import AlumInfo
from .models import AlumSurvey
from .models import ApplicantApproval
from .models import ApplicantGenderIdentity
from .models import ApplicantRaceEthnicityInformation
from .models import ApplicationReviewer
from .models import BarriersToParticipation
from .models import PriorFOSSExperience
from .models import ContractorInformation
from .models import CommunicationChannel
from .models import Community
from .models import Comrade
from .models import Contribution
from .models import CoordinatorApproval
from .models import EmploymentTimeCommitment
from .models import EssayQuality
from .models import FinalApplication
from .models import FinalInternFeedback
from .models import FinalMentorFeedback
from .models import InformalChatContact
from .models import InternSelection
from .models import Feedback1FromMentor
from .models import Feedback1FromIntern
from .models import Feedback2FromMentor
from .models import Feedback2FromIntern
from .models import Feedback3FromMentor
from .models import Feedback3FromIntern
from .models import Feedback4FromMentor
from .models import Feedback4FromIntern
from .models import MentorApproval
from .models import MentorRelationship
from .models import NewCommunity
from .models import NonCollegeSchoolTimeCommitment
from .models import Notification
from .models import OfficialSchool
from .models import OfficialSchoolTerm
from .models import Participation
from .models import PaymentEligibility
from .models import Project
from .models import ProjectSkill
from .models import PromotionTracking
from .models import RoundPage
from .models import SchoolInformation
from .models import SchoolTimeCommitment
from .models import SignedContract
from .models import Sponsorship
from .models import TimeCommitmentSummary
from .models import VolunteerTimeCommitment
from .models import WorkEligibility

class ComradeInline(admin.StackedInline):
    model = Comrade
    can_delete = False
    verbose_name_plural = 'comrade'

class ComradeAdmin(UserAdmin):
    inlines = (ComradeInline, )

class AlumInfoAdmin(reversion.admin.VersionAdmin):
    model = AlumInfo
    list_display = (
            'name',
            'community',
            'round_string',
            )
    list_filter = (
            'community',
            'page__round_start',
            )

class AlumSurveyAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'survey_date',
            'intern_name',
            'community',
            )
    list_filter = (
            'survey_date',
            'survey_tracker__intern_info__project__project_round__community__name',
            'survey_tracker__alumni_info__community',
            'survey_tracker__intern_info__project__project_round__participating_round__internstarts',
            'survey_tracker__alumni_info__page__round_start',
            )
    search_fields = (
            'survey_date',
            'intern_info__project__project_round__community__name',
            'alumni_info__community',
            'intern_info__applicant__applicant__public_name',
            'alumni_info__name',
            'intern_info__applicant__applicant__legal_name',
            'intern_info__applicant__applicant__account__email',
            'alumni_info__email',
            'intern_info__applicant__applicant__account__username',
            )

class OnlyComradeAdmin(reversion.admin.VersionAdmin):
    model = Comrade
    list_display = (
            'public_name',
            'location',
            'timezone',
            )
    search_fields = (
            'public_name',
            'legal_name',
            'account__username',
            'account__email',
            )
    list_display = (
            'public_name',
            'username',
            'email_address',
            )
    raw_id_fields = (
            'account',
            )

class RoundPageAdmin(reversion.admin.VersionAdmin):
    model = RoundPage
    list_display = (
            'official_name',
            'internstarts',
            'internends',
            )
    search_fields = (
            'internstarts',
            'internends',
            )

class SponsorshipInline(admin.StackedInline):
    model = Sponsorship

class ParticipationAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'community',
            'approval_status',
            'round',
            )
    list_filter = (
            'approval_status',
            'participating_round',
            )
    search_fields = (
            'community__name',
            )
    raw_id_fields =  (
            'community',
            'participating_round',
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
            )
    list_filter = (
            'rounds',
            )
    search_fields = (
            'name',
            'website',
            'description',
            )


class ProjectSkillAdmin(reversion.admin.VersionAdmin):
    model = ProjectSkill
    verbose_name_plural = 'Project Skills'
    list_display = (
            'skill',
            )
    ordering = ['skill']
    list_filter = (
            'project__project_round__participating_round',
            'project__project_round__community',
            )
    search_fields = (
            'skill',
            'project__project_round__community__name',
            )
    raw_id_fields = (
            'project',
            )
    actions = ['rename_project_skills']

    def rename_project_skills(modeladmin, request, queryset):
        selected_objects = queryset.values_list('pk', flat=True)
        # Redirect to a page that renames all skills with old name to new name
        return redirect(reverse('rename-project-skills') + '?ids={}'.format(','.join([str(pk) for pk in selected_objects])))

class SkillsInline(admin.StackedInline):
    model = ProjectSkill
    can_delete = False
    verbose_name_plural = 'Project Skills'

class ChannelsInline(admin.StackedInline):
    model = CommunicationChannel
    can_delete = False
    verbose_name_plural = 'Communication Channels'

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
    raw_id_fields = (
            'project_round',
            )
    inlines = (ChannelsInline, SkillsInline)

    def community(self, obj):
        return obj.project_round.community.name
    community.admin_order_field = 'project_round__community__name'

    def round(self, obj):
        return obj.round()
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
    raw_id_fields = (
            'mentor',
            'project',
            )

    def project_name(self, obj):
        return obj.project.short_title

    def community(self, obj):
        return obj.project.project_round.community.name
    community.admin_order_field = 'project__project_round__community__name'

    def round(self, obj):
        return obj.project.round()
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
    raw_id_fields = (
            'coordinator',
            'community',
            )

class ApplicationReviewerAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'comrade',
            'reviewing_round',
            'approval_status',
            )
    list_filter = (
            'approval_status',
            'reviewing_round',
            )
    search_fields = (
            'comrade__public_name',
            '=comrade__account__username',
            '=comrade__account__email',
            )
    raw_id_fields = (
            'comrade',
            'reviewing_round',
            )

class EssayQualityAdmin(admin.ModelAdmin):
    list_display = (
            'category',
            'description',
            )
    list_filter = (
            'category',
            )
    search_fields = (
            'description',
            )
    verbose_name_plural = 'Essay Qualities'

class WorkEligibilityInline(admin.StackedInline):
    model = WorkEligibility
    can_delete = False
    extra = 1
    verbose_name_plural = 'Work Eligibility'

class PaymentEligibilityInline(admin.StackedInline):
    model = PaymentEligibility
    can_delete = False
    extra = 1
    verbose_name_plural = 'Payment Eligibility'

class ApplicantGenderIdentityInline(admin.StackedInline):
    model = ApplicantGenderIdentity
    can_delete = False
    extra = 1
    verbose_name_plural = 'Gender Identity'

class ApplicantRaceEthnicityInformationInline(admin.StackedInline):
    model = ApplicantRaceEthnicityInformation
    can_delete = False
    extra = 1
    verbose_name_plural = 'Race and Ethnicity'

class BarriersToParticipationInline(admin.StackedInline):
    model = BarriersToParticipation
    can_delete = False
    extra = 1
    verbose_name_plural = 'Barriers to Participation'

class PriorFOSSExperienceInline(admin.StackedInline):
    model = PriorFOSSExperience
    can_delete = False
    extra = 1
    verbose_name_plural = 'Prior FOSS Experience'

class TimeCommitmentSummaryInline(admin.StackedInline):
    model = TimeCommitmentSummary
    can_delete = False
    extra = 1

class SchoolInformationInline(admin.StackedInline):
    model = SchoolInformation
    can_delete = False
    extra = 1
    verbose_name_plural = 'School information'

class SchoolTimeCommitmentsInline(admin.StackedInline):
    model = SchoolTimeCommitment
    can_delete = False
    extra = 1
    verbose_name_plural = 'School term'

class NonCollegeSchoolTimeCommitmentsInline(admin.StackedInline):
    model = NonCollegeSchoolTimeCommitment
    can_delete = False
    extra = 1
    verbose_name_plural = 'Coding school or online courses'

class EmploymentTimeCommitmentsInline(admin.StackedInline):
    model = EmploymentTimeCommitment
    can_delete = False
    extra = 1
    verbose_name_plural = 'Employment period'

class ContractorInformationInline(admin.StackedInline):
    model = ContractorInformation
    can_delete = False
    extra = 1
    verbose_name_plural = 'Contractor Information'

class VolunteerTimeCommitmentsInline(admin.StackedInline):
    model = VolunteerTimeCommitment
    can_delete = False
    extra = 1
    verbose_name_plural = 'Time commitment'

class ContributionsInline(admin.StackedInline):
    model = Contribution
    can_delete = True
    extra = 1
    verbose_name_plural = 'Project contributions'
    raw_id_fields = (
        'project',
    )

class ApplicationsInline(admin.StackedInline):
    model = FinalApplication
    can_delete = True
    extra = 1
    verbose_name_plural = 'Final application'
    raw_id_fields = (
        'project',
    )

class PromotionTrackingInline(admin.StackedInline):
    model = PromotionTracking
    can_delete = False
    extra = 1
    verbose_name_plural = 'Promotion tracking'

class ApplicantApprovalAdmin(admin.ModelAdmin):
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
            'applicant__legal_name',
            '=applicant__account__username',
            '=applicant__account__email',
            )

    readonly_fields = (
        'applicant',
        'application_round',
        'ip_address',
    )
    raw_id_fields = (
        'review_owner',
        )

    inlines = (WorkEligibilityInline, PaymentEligibilityInline, ApplicantGenderIdentityInline, ApplicantRaceEthnicityInformationInline, PriorFOSSExperienceInline, BarriersToParticipationInline, TimeCommitmentSummaryInline, SchoolInformationInline, SchoolTimeCommitmentsInline, NonCollegeSchoolTimeCommitmentsInline, EmploymentTimeCommitmentsInline, ContractorInformationInline, VolunteerTimeCommitmentsInline, ContributionsInline, ApplicationsInline, PromotionTrackingInline)

    def round(self, obj):
        return obj.application_round
    round.admin_order_field = '-application_round__roundnumber'

class OfficialSchoolTermInline(admin.StackedInline):
    model = OfficialSchoolTerm
    can_delete = True
    verbose_name_plural = 'Official School Terms'

class OfficialSchoolAdmin(admin.ModelAdmin):
    list_display = (
            'university_name',
            'university_website',
            )
    search_fields = (
            'university_name',
            'university_website',
            )
    inlines = (OfficialSchoolTermInline, )

class BarriersToParticipationAdmin(admin.ModelAdmin):
    model = AlumInfo
    list_display = (
            'applicant',
            'applicant_should_update',
            )
    list_filter = (
            'applicant__approval_status',
            'applicant_should_update',
            'applicant__application_round__internstarts',
            )
    search_fields = (
            'applicant__public_name',
            'applicant__legal_name',
            '=applicant__account__username',
            '=applicant__account__email',
            )

class ContributionAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'applicant',
            'project',
            )
    list_filter = (
            'project__project_round__participating_round',
            'project__project_round__community',
            'project',
            )
    search_fields = (
            'applicant__applicant__public_name',
            'applicant__applicant__legal_name',
            '=applicant__applicant__account__username',
            '=applicant__applicant__account__email',
            )
    raw_id_fields = (
            'applicant',
            'project',
            )

class FinalApplicationAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'applicant',
            'project',
            )
    list_filter = (
            'approval_status',
            'project__project_round__participating_round',
            'project__project_round__community',
            'project',
            )
    search_fields = (
            'applicant__applicant__public_name',
            'applicant__applicant__legal_name',
            '=applicant__applicant__account__username',
            '=applicant__applicant__account__email',
            )
    raw_id_fields = (
            'applicant',
            'project'
            )

class MentorRelationshipAdmin(admin.ModelAdmin):
    list_display = (
            'round',
            'community_name',
            'project_name',
            'intern_name',
            'mentor_name',
            )
    list_filter = (
            'intern_selection__project__project_round__participating_round',
            'intern_selection__project__project_round__community__name',
            'intern_selection__organizer_approved',
            'intern_selection__funding_source',
            )
    search_fields = (
            'intern_selection__applicant__applicant__public_name',
            'intern_selection__applicant__applicant__legal_name',
            'intern_selection__applicant__applicant__account__email',
            'intern_selection__applicant__applicant__account__username',
            )
    raw_id_fields = (
            'intern_selection',
            'mentor',
            'contract',
            )

class SignedContractAdmin(admin.ModelAdmin):
    list_display = (
            'legal_name',
            'date_signed',
            )
    search_fields = (
            'legal_name',
            'date_signed',
            )

class Feedback1FromMentorInline(admin.StackedInline):
    model = Feedback1FromMentor
    can_delete = False
    verbose_name_plural = 'Feedback #1 from mentor'

class Feedback1FromInternInline(admin.StackedInline):
    model = Feedback1FromIntern
    can_delete = False
    verbose_name_plural = 'Feedback #2 from intern'

class Feedback2FromMentorInline(admin.StackedInline):
    model = Feedback2FromMentor
    can_delete = False
    verbose_name_plural = 'Mentor submitted midpoint feedback forms'

class Feedback2FromInternInline(admin.StackedInline):
    model = Feedback2FromIntern
    can_delete = False
    verbose_name_plural = 'Intern submitted midpoint feedback forms'

class Feedback3FromMentorInline(admin.StackedInline):
    model = Feedback3FromMentor
    can_delete = False
    verbose_name_plural = 'Feedback #3 from mentor'

class Feedback3FromInternInline(admin.StackedInline):
    model = Feedback3FromIntern
    can_delete = False
    verbose_name_plural = 'Feedback #3 from intern'

class Feedback4FromMentorInline(admin.StackedInline):
    model = Feedback4FromMentor
    can_delete = False
    verbose_name_plural = 'Feedback #4 from mentor'

class Feedback4FromInternInline(admin.StackedInline):
    model = Feedback4FromIntern
    can_delete = False
    verbose_name_plural = 'Feedback #4 from intern'

class InternSelectionAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'round',
            'community_name',
            'project_name',
            'intern_name',
            'mentor_names',
            )
    list_filter = (
            'project__project_round__participating_round',
            'project__project_round__community__name',
            'organizer_approved',
            'funding_source',
            )
    search_fields = (
            'applicant__applicant__public_name',
            'applicant__applicant__account__email',
            'mentors__mentor__public_name',
            'mentors__mentor__account__email',
            )
    raw_id_fields = (
            'applicant',
            'project',
            'intern_contract',
            )
    inlines = (Feedback1FromMentorInline, Feedback1FromInternInline, Feedback2FromMentorInline, Feedback2FromInternInline, Feedback3FromMentorInline, Feedback3FromInternInline, Feedback4FromMentorInline, Feedback4FromInternInline)

class FeedbackAdmin(reversion.admin.VersionAdmin):
    list_display = (
            'intern_name',
            'community_name',
            'project_name',
            'round',
            )
    list_filter = (
            'intern_selection__project__project_round__participating_round',
            'intern_selection__project__project_round__community__name',
            )
    search_fields = (
            'intern_selection__applicant__applicant__public_name',
            'intern_selection__applicant__applicant__legal_name',
            '=intern_selection__applicant__applicant__account__username',
            '=intern_selection__applicant__applicant__account__email',
            )

class InformalChatContactAdmin(reversion.admin.VersionAdmin):
    model = AlumInfo
    list_display = (
            'name',
            'email',
            'comrade',
            )
    raw_id_fields = (
        'comrade',
        )
    search_fields = (
            'name',
            'email',
            'comrade__public_name',
            'comrade__legal_name',
            '=comrade__account__email',
            'relationship_to_outreachy',
            'foss_communities',
            'paid_foss_roles',
            'volunteer_foss_roles',
            'company',
            )

admin.site.unregister(User)
admin.site.register(User, ComradeAdmin)

admin.site.register(AlumInfo, AlumInfoAdmin)
admin.site.register(AlumSurvey, AlumSurveyAdmin)
admin.site.register(ApplicantApproval, ApplicantApprovalAdmin)
admin.site.register(ApplicationReviewer, ApplicationReviewerAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(Comrade, OnlyComradeAdmin)
admin.site.register(CoordinatorApproval, CoordinatorApprovalAdmin)
admin.site.register(Contribution, ContributionAdmin)
admin.site.register(EssayQuality, EssayQualityAdmin)
admin.site.register(FinalApplication, FinalApplicationAdmin)
admin.site.register(InformalChatContact, InformalChatContactAdmin)
admin.site.register(InternSelection, InternSelectionAdmin)
admin.site.register(MentorApproval, MentorApprovalAdmin)
admin.site.register(MentorRelationship, MentorRelationshipAdmin)
admin.site.register(NewCommunity, CommunityAdmin)
admin.site.register(Notification)
admin.site.register(OfficialSchool, OfficialSchoolAdmin)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RoundPage, RoundPageAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectSkill, ProjectSkillAdmin)
admin.site.register(SignedContract, SignedContractAdmin)
