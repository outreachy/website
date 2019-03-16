from betterforms.multiform import MultiModelForm
from datetime import datetime, timedelta, timezone, date
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.core.exceptions import PermissionDenied
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature 
from django.db import models
from django.forms import inlineformset_factory, ModelForm, modelform_factory, modelformset_factory, ValidationError
from django.forms.models import BaseInlineFormSet, BaseModelFormSet
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import FormView, View, DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from formtools.wizard.views import SessionWizardView
from itertools import chain, groupby
from markdownx.utils import markdownify
from registration.forms import RegistrationForm
from registration.backends.hmac import views as hmac_views
import reversion

from . import email

from .dashboard import get_dashboard_sections

from .forms import RadioBooleanField

from .mixins import ApprovalStatusAction
from .mixins import ComradeRequiredMixin
from .mixins import EligibleApplicantRequiredMixin
from .mixins import Preview

from .models import AlumInfo
from .models import AlumSurvey
from .models import AlumSurveyTracker
from .models import ApplicantApproval
from .models import ApplicantGenderIdentity
from .models import ApplicantRaceEthnicityInformation
from .models import ApplicationReviewer
from .models import ApprovalStatus
from .models import BarriersToParticipation
from .models import CohortPage
from .models import CommunicationChannel
from .models import Community
from .models import Comrade
from .models import ContractorInformation
from .models import Contribution
from .models import CoordinatorApproval
from .models import create_time_commitment_calendar
from .models import EmploymentTimeCommitment
from .models import FinalApplication
from .models import get_deadline_date_for
from .models import InternSelection
from .models import InitialApplicationReview
from .models import InitialMentorFeedback
from .models import InitialInternFeedback
from .models import MidpointMentorFeedback
from .models import MidpointInternFeedback
from .models import FinalMentorFeedback
from .models import FinalInternFeedback
from .models import has_deadline_passed
from .models import MentorApproval
from .models import MentorRelationship
from .models import NewCommunity
from .models import NonCollegeSchoolTimeCommitment
from .models import Notification
from .models import Participation
from .models import PaymentEligibility
from .models import PriorFOSSExperience
from .models import Project
from .models import ProjectSkill
from .models import PromotionTracking
from .models import Role
from .models import RoundPage
from .models import SchoolInformation
from .models import SchoolTimeCommitment
from .models import TimeCommitmentSummary
from .models import SignedContract
from .models import Sponsorship
from .models import VolunteerTimeCommitment
from .models import WorkEligibility

from os import path

class RegisterUserForm(RegistrationForm):
    def clean(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', mark_safe('This email address is already associated with an account. If you have forgotten your password, you can <a href="{}">reset it</a>.'.format(reverse('password_reset'))))
        super(RegisterUserForm, self).clean()

class RegisterUser(hmac_views.RegistrationView):
    form_class = RegisterUserForm

    # The RegistrationView that django-registration provides
    # doesn't respect the next query parameter, so we have to
    # add it to the context of the template.
    def get_context_data(self, **kwargs):
        context = super(RegisterUser, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
        return context

    def get_activation_key(self, user):
        # The superclass implementation of get_activation_key will
        # serialize arbitrary data in JSON format, so we can save more
        # data than just the username, which is good! Unfortunately it
        # expects to get that data from the field named after whatever
        # string is in USERNAME_FIELD, which only works for actual
        # Django user models. So first we construct a fake user model
        # for it to take apart, containing only the data we want.
        self.USERNAME_FIELD = 'activation_data'
        self.activation_data = {'u': user.username}

        # Now, if we have someplace the user is supposed to go after
        # registering, then we save that as well.
        next_url = self.request.POST.get('next')
        if next_url:
            self.activation_data['n'] = next_url

        return super(RegisterUser, self).get_activation_key(self)

    def get_email_context(self, activation_key):
        return {
            'activation_key': activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'request': self.request,
        }

class PendingRegisterUser(TemplateView):
    template_name = 'registration/registration_complete.html'

class ActivationView(hmac_views.ActivationView):
    def get_user(self, data):
        # In the above RegistrationView, we dumped extra data into the
        # activation key, but the superclass implementation of get_user
        # expects the key to contain only a username string. So we save
        # our extra data and then pass the superclass the part it
        # expected.
        self.next_url = data.get('n')
        return super(ActivationView, self).get_user(data['u'])

    def get_success_url(self, user):
        # Ugh, we need to chain together TWO next-page URLs so we can
        # confirm that the person who posesses this activation token
        # also knows the corresponding password, then make a stop at the
        # ComradeUpdate form, before finally going where the user
        # actually wanted to go. Sorry folks.
        if self.next_url:
            query = '?' + urlencode({'next': self.next_url})
        else:
            query = ''
        query = '?' + urlencode({'next': reverse('account') + query})
        return reverse('registration_activation_complete') + query

class ActivationCompleteView(TemplateView):
    template_name = 'registration/activation_complete.html'

class ComradeUpdate(LoginRequiredMixin, UpdateView):
    # FIXME - we need a way for comrades to change their passwords
    # and update and re-verify their email address.

    def get_form_class(self):
        # We want to have different fields for different comrades, but
        # self.fields is shared across all instances of this view, so we can't
        # use that. There's no get_fields() method we can override, either, so
        # the only hook we can use is overriding this method of ModelFormMixin.
        fields = [
            'public_name',
            'nick_name',
            'legal_name',
            'pronouns',
            'pronouns_to_participants',
            'pronouns_public',
        ]

        comrade = self.object

        # was an approved coordinator for a community that had at least one approved participation
        coordinatored = comrade.coordinatorapproval_set.approved().filter(
            community__participation__approval_status=ApprovalStatus.APPROVED,
        )
        # was an approved mentor for some approved project in an approved community
        mentored = comrade.get_mentored_projects().approved().filter(
            project_round__approval_status=ApprovalStatus.APPROVED,
        )
        # was an approved application reviewer at some point
        reviewered = comrade.applicationreviewer_set.approved()

        # people who participated in some way at some time can set a photo of themselves
        if comrade.account.is_staff or comrade.get_intern_selection() is not None or coordinatored.exists() or mentored.exists() or reviewered.exists():
            fields.append('photo')

        fields.extend([
            'timezone',
            'location',
            'nick',
            'github_url',
            'gitlab_url',
            'blog_url',
            'blog_rss_url',
            'twitter_url',
            'agreed_to_code_of_conduct',
        ])
        return modelform_factory(comrade.__class__, fields=fields)

    def get_object(self):
        # Either grab the current comrade to update, or make a new one
        try:
            return self.request.user.comrade
        except Comrade.DoesNotExist:
            return Comrade(account=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ComradeUpdate, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
        with open(path.join(settings.BASE_DIR, 'CODE-OF-CONDUCT.md')) as coc_file:
            context['codeofconduct'] = markdownify(coc_file.read())
        return context

    # FIXME - not sure where we should redirect people back to?
    # Take them back to the home page right now.
    def get_success_url(self):
        return self.request.POST.get('next', '/')

class EmptyModelFormSet(BaseModelFormSet):
    def get_queryset(self):
        return self.model._default_manager.none()

class SchoolTimeCommitmentModelFormSet(EmptyModelFormSet):
    def clean(self):
        super(SchoolTimeCommitmentModelFormSet, self).clean()
        if any(self.errors):
            # Don't validate if the individual term fields already have errors
            return

        end = None
        last_term = None
        number_filled_terms = 0
        for index, form in enumerate(self.forms):
            # This checks if one of the forms was left blank
            if index >= self.initial_form_count() and not form.has_changed():
                continue
            number_filled_terms += 1

            # Ensure that only one term has last_term set
            end_term = form.cleaned_data['last_term']
            if end_term:
                if last_term:
                    raise ValidationError("You cannot have more than one term be the last term in your degree.")
                else:
                    last_term = form

            # Ensure terms are in consecutive order
            start_date = form.cleaned_data['start_date']
            if end and end > start_date:
                raise ValidationError("Terms must be in chronological order.")
            end = form.cleaned_data['end_date']

        # Ensure that all three terms are filled out, unless one term has the last_term set
        if not last_term and number_filled_terms < 3:
            raise ValidationError("Please provide information for your next three terms of classes.")

        # We can't confirm there are no terms after the term where last_term is set
        # because someone might be ending their bachelor's degree and starting a master's.

def work_eligibility_is_approved(wizard):
    cleaned_data = wizard.get_cleaned_data_for_step('Work Eligibility')
    if not cleaned_data:
        return True
    if not cleaned_data['over_18']:
        return False
    # If they have student visa restrictions, we don't follow up
    # until they're actually selected as an intern, at which point we
    # need to send them a CPT letter and have them get it approved.
    if not cleaned_data['eligible_to_work']:
        return False
    if cleaned_data['under_export_control']:
        return False
    # If they're in a us_sanctioned_country, go ahead and collect the
    # rest of the information on the forms, but we'll mark them as
    # PENDING later.
    return True

def prior_foss_experience_is_approved(wizard):
    if not work_eligibility_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Prior FOSS Experience')
    if not cleaned_data:
        return True
    if cleaned_data['gsoc_or_outreachy_internship']:
        return False
    return True

def show_us_demographics(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Payment Eligibility') or {}
    if not cleaned_data:
        return True
    us_resident = cleaned_data.get('us_national_or_permanent_resident', True)
    return us_resident

def show_noncollege_school_info(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('enrolled_as_noncollege_student', True)

def show_school_info(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('enrolled_as_student', True)

def show_contractor_info(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    if cleaned_data == None:
        return False
    return cleaned_data.get('contractor', True)

def show_employment_info(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    if cleaned_data.get('employed', True):
        return True
    if cleaned_data.get('contractor', True):
        cleaned_data = wizard.get_cleaned_data_for_step('Contractor Info')
        if cleaned_data and cleaned_data[0].get('continuing_contract_work', True):
            return True
    return False

def show_time_commitment_info(wizard):
    if not prior_foss_experience_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('volunteer_time_commitments', True)

def time_commitment(cleaned_data, hours):
    return {
            'start_date': cleaned_data['start_date'],
            'end_date': cleaned_data['end_date'],
            'hours': hours,
            }

def time_commitments_are_approved(wizard, application_round):
    tcs = [ time_commitment(d, d['hours_per_week'])
            for d in wizard.get_cleaned_data_for_step('Volunteer Time Commitment Info') or []
            if d ]

    ctcs = [ time_commitment(d, 0 if d['quit_on_acceptance'] else d['hours_per_week'])
            for d in wizard.get_cleaned_data_for_step('Coding School or Online Courses Time Commitment Info') or []
            if d ]

    etcs = [ time_commitment(d, 0 if d['quit_on_acceptance'] else d['hours_per_week'])
            for d in wizard.get_cleaned_data_for_step('Employment Info') or []
            if d ]

    stcs = [ time_commitment(d, 40)
            for d in wizard.get_cleaned_data_for_step('School Term Info') or []
            if d ]

    required_free_days = 7*7
    calendar = create_time_commitment_calendar(chain(tcs, ctcs, etcs, stcs), application_round)

    for key, group in groupby(calendar, lambda hours: hours <= 20):
        if key is True and len(list(group)) >= required_free_days:
            return True
    return False

def determine_eligibility(wizard, application_round):
    if not (work_eligibility_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'GENERAL')
    if not (prior_foss_experience_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'GENERAL')
    if not time_commitments_are_approved(wizard, application_round):
        return (ApprovalStatus.REJECTED, 'TIME')

    general_data = wizard.get_cleaned_data_for_step('Work Eligibility')
    if general_data['us_sanctioned_country']:
        return (ApprovalStatus.PENDING, 'SANCTIONED')

    return (ApprovalStatus.PENDING, 'ESSAY')

# People can only submit new initial applications or edit initial applications
# when the application period is open.
def get_current_round_for_initial_application():
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        return RoundPage.objects.get(
            appsopen__lte=today,
            appslate__gt=today,
        )
    except RoundPage.DoesNotExist:
        raise PermissionDenied('The Outreachy application period is closed. If you are an applicant who has submitted an application for an internship project and your time commitments have increased, please contact the Outreachy organizers (see contact link above). Eligibility checking will become available when the next application period opens. Please sign up for the announcements mailing list for an email when the next application period opens: https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce')

class EligibilityUpdateView(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, SessionWizardView):
    template_name = 'home/wizard_form.html'
    condition_dict = {
            'Payment Eligibility': work_eligibility_is_approved,
            'Prior FOSS Experience': work_eligibility_is_approved,
            'USA demographics': show_us_demographics,
            'Gender Identity': prior_foss_experience_is_approved,
            'Time Commitments': prior_foss_experience_is_approved,
            'School Info': show_school_info,
            'School Term Info': show_school_info,
            'Coding School or Online Courses Time Commitment Info': show_noncollege_school_info,
            'Contractor Info': show_contractor_info,
            'Employment Info': show_employment_info,
            'Volunteer Time Commitment Info': show_time_commitment_info,
            }
    form_list = [
            ('Work Eligibility', modelform_factory(WorkEligibility,
                fields=(
                'over_18',
                'student_visa_restrictions',
                'eligible_to_work',
                'under_export_control',
                'us_sanctioned_country',
                ),
                field_classes={
                    'over_18': RadioBooleanField,
                    'student_visa_restrictions': RadioBooleanField,
                    'eligible_to_work': RadioBooleanField,
                    'under_export_control': RadioBooleanField,
                    'us_sanctioned_country': RadioBooleanField,
                },
            )),
            ('Payment Eligibility', modelform_factory(PaymentEligibility,
                fields=(
                'us_national_or_permanent_resident',
                'living_in_us',
                ),
                field_classes={
                    'us_national_or_permanent_resident': RadioBooleanField,
                    'living_in_us': RadioBooleanField,
                },
            )),
            ('Prior FOSS Experience', modelform_factory(PriorFOSSExperience,
                fields=(
                'gsoc_or_outreachy_internship',
                'prior_contributor',
                'prior_paid_contributor',
                'prior_contrib_coding',
                'prior_contrib_forums',
                'prior_contrib_events',
                'prior_contrib_issues',
                'prior_contrib_devops',
                'prior_contrib_docs',
                'prior_contrib_data',
                'prior_contrib_translate',
                'prior_contrib_illustration',
                'prior_contrib_ux',
                'prior_contrib_short_talk',
                'prior_contrib_testing',
                'prior_contrib_security',
                'prior_contrib_marketing',
                'prior_contrib_reviewer',
                'prior_contrib_mentor',
                'prior_contrib_accessibility',
                'prior_contrib_self_identify',
                ),
                field_classes={
                    'gsoc_or_outreachy_internship': RadioBooleanField,
                    'prior_contributor': RadioBooleanField,
                    'prior_paid_contributor': RadioBooleanField,
                },
            )),
            ('USA demographics', modelform_factory(ApplicantRaceEthnicityInformation,
                fields=(
                'us_resident_demographics',
                ),
                field_classes={
                    'us_resident_demographics': RadioBooleanField,
                },
            )),
            ('Gender Identity', modelform_factory(ApplicantGenderIdentity, fields=(
                'transgender',
                'genderqueer',
                'man',
                'woman',
                'demi_boy',
                'demi_girl',
                'trans_masculine',
                'trans_feminine',
                'non_binary',
                'demi_non_binary',
                'genderqueer',
                'genderflux',
                'genderfluid',
                'demi_genderfluid',
                'demi_gender',
                'bi_gender',
                'tri_gender',
                'multigender',
                'pangender',
                'maxigender',
                'aporagender',
                'intergender',
                'mavrique',
                'gender_confusion',
                'gender_indifferent',
                'graygender',
                'agender',
                'genderless',
                'gender_neutral',
                'neutrois',
                'androgynous',
                'androgyne',
                'prefer_not_to_say',
                'self_identify',
                ),
                field_classes={
                    'transgender': RadioBooleanField,
                    'genderqueer': RadioBooleanField,
                },
            )),
            ('Barriers to Participation', modelform_factory(BarriersToParticipation,
                fields=(
                    'lacking_representation',
                    'systemic_bias',
                    'employment_bias',
                    'barriers_to_contribution',
                ),
            )),
            ('Time Commitments', modelform_factory(TimeCommitmentSummary,
                fields=(
                'enrolled_as_student',
                'enrolled_as_noncollege_student',
                'employed',
                'contractor',
                'volunteer_time_commitments',
                ),
                field_classes={
                    'enrolled_as_student': RadioBooleanField,
                    'enrolled_as_noncollege_student': RadioBooleanField,
                    'employed': RadioBooleanField,
                    'contractor': RadioBooleanField,
                    'volunteer_time_commitments': RadioBooleanField,
                },
            )),
            ('School Info', modelform_factory(SchoolInformation,
                fields=(
                    'university_name',
                    'university_website',
                    'current_academic_calendar',
                    'next_academic_calendar',
                    'degree_name',
                ),
            )),
            ('School Term Info', modelformset_factory(SchoolTimeCommitment,
                formset=SchoolTimeCommitmentModelFormSet,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'term_name',
                    'start_date',
                    'end_date',
                    'last_term',
                ),
            )),
            ('Coding School or Online Courses Time Commitment Info', modelformset_factory(NonCollegeSchoolTimeCommitment,
                formset=EmptyModelFormSet,
                min_num=1,
                validate_min=True,
                extra=4,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'description',
                    'quit_on_acceptance',
                ),
            )),
            ('Contractor Info', modelformset_factory(ContractorInformation,
                formset=EmptyModelFormSet,
                min_num=1,
                max_num=1,
                validate_min=True,
                validate_max=True,
                can_delete=False,
                fields=(
                    'typical_hours',
                    'continuing_contract_work',
                ),
                field_classes={
                    'continuing_contract_work': RadioBooleanField,
                },
            )),
            ('Employment Info', modelformset_factory(EmploymentTimeCommitment,
                formset=EmptyModelFormSet,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'job_title',
                    'job_description',
                    'quit_on_acceptance',
                ),
            )),
            ('Volunteer Time Commitment Info', modelformset_factory(VolunteerTimeCommitment,
                formset=EmptyModelFormSet,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'description',
                ),
            )),
            ('Outreachy Promotional Information', modelform_factory(PromotionTracking,
                fields=(
                'spread_the_word',
                ),
            )),
        ]
    TEMPLATES = {
            'Work Eligibility': 'home/eligibility_wizard_general.html',
            'Payment Eligibility': 'home/eligibility_wizard_tax_forms.html',
            'Prior FOSS Experience': 'home/eligibility_wizard_foss_experience.html',
            'USA demographics': 'home/eligibility_wizard_us_demographics.html',
            'Gender Identity': 'home/eligibility_wizard_gender.html',
            'Barriers to Participation': 'home/eligibility_wizard_essay_questions.html',
            'Time Commitments': 'home/eligibility_wizard_time_commitments.html',
            'School Info': 'home/eligibility_wizard_school_info.html',
            'School Term Info': 'home/eligibility_wizard_school_terms.html',
            'Coding School or Online Courses Time Commitment Info': 'home/eligibility_wizard_noncollege_school_info.html',
            'Contractor Info': 'home/eligibility_wizard_contractor_info.html',
            'Employment Info': 'home/eligibility_wizard_employment_info.html',
            'Volunteer Time Commitment Info': 'home/eligibility_wizard_time_commitment_info.html',
            'Outreachy Promotional Information': 'home/eligibility_wizard_promotional.html',
            }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def show_results_if_any(self):
        # get_context_data() and done() both need a round; save it for them.
        self.current_round = get_current_round_for_initial_application()

        already_submitted = ApplicantApproval.objects.filter(
            applicant=self.request.user.comrade,
            application_round=self.current_round,
        ).exists()

        if not already_submitted:
            # Continue with the default get or post behavior.
            return None

        return redirect(self.request.GET.get('next', reverse('eligibility-results')))

    def get(self, *args, **kwargs):
        # Using `or` this way returns the redirect from show_results_if_any,
        # unless that function returns None. Only in that case does it call the
        # superclass implementation of this method and return _that_.
        return self.show_results_if_any() or super(EligibilityUpdateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        # See self.get(), above.
        return self.show_results_if_any() or super(EligibilityUpdateView, self).post(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EligibilityUpdateView, self).get_context_data(**kwargs)
        context['current_round'] = self.current_round
        return context

    def done(self, form_list, **kwargs):

        self.object = ApplicantApproval(
            applicant=self.request.user.comrade,
            application_round=self.current_round,
        )
        self.object.ip_address = self.request.META.get('REMOTE_ADDR')

        # It's okay that the other objects aren't saved,
        # because determine_eligibility get the cleaned data from the form wizard,
        # not the database objects.
        self.object.approval_status, self.object.reason_denied = determine_eligibility(self, self.object.application_round)
        # Make sure to commit the object to the database before saving
        # any of the related objects, so they can set their foreign keys
        # to point to this ApplicantApproval object.
        self.object.save()

        for form in form_list:
            results = form.save(commit=False)

            # result might be a single value because it's a modelform
            # (WorkEligibility and TimeCommitmentSummary)
            # or a list because it's a modelformsets
            # (VolunteerTimeCommitment, EmploymentTimeCommitment, etc)
            # The next line is magic to check if it's a list
            if not isinstance(results, list):
                results = [ results ]

            # For each object which contains data from the modelform
            # or modelformsets, we save that database object,
            # after setting the parent pointer.
            for r in results:
                r.applicant = self.object
                r.save()

        return redirect(self.request.GET.get('next', reverse('eligibility-results')))

class EligibilityResults(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/eligibility_results.html'
    context_object_name = 'application'

    def get_object(self):
        current_round = get_current_round_for_initial_application()
        return get_object_or_404(ApplicantApproval,
                    applicant=self.request.user.comrade,
                    application_round=current_round)

    def get_context_data(self, **kwargs):
        context = super(EligibilityResults, self).get_context_data(**kwargs)
        context.update(self.object.get_time_commitments())
        context['current_round'] = self.object.application_round
        return context

class ViewInitialApplication(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/applicant_review_detail.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super(ViewInitialApplication, self).get_context_data(**kwargs)
        context['current_round'] = self.object.application_round
        context['role'] = self.role
        return context

    def get_object(self):
        current_round = get_current_round_for_initial_application()

        self.role = Role(self.request.user, current_round)

        if not self.role.is_organizer and not self.role.is_reviewer:
            raise PermissionDenied("You are not authorized to review applications.")

        return get_object_or_404(ApplicantApproval,
                    applicant__account__username=self.kwargs['applicant_username'],
                    application_round=current_round)

def past_rounds_page(request):
    return render(request, 'home/past_rounds.html',
            {
                'rounds' : RoundPage.objects.all().order_by('internstarts'),
            },
            )

def current_round_page(request):
    closed_approved_projects = []
    ontime_approved_projects = []
    late_approved_projects = []
    example_skill = ProjectSkill

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        previous_round = RoundPage.objects.filter(
            appslate__lte=today,
        ).latest('internstarts')
    except RoundPage.DoesNotExist:
        previous_round = None

    try:
        # Keep RoundPage.serve() in sync with this.
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            # If the application period is closed, don't show projects from the current round
            appslate__gt=today,
        )
    except RoundPage.DoesNotExist:
        current_round = None

    role = Role(request.user, current_round, today=today)
    if current_round is not None:
        approved_participations = current_round.participation_set.approved().order_by('community__name')

        for p in approved_participations:
            if not p.approved_to_see_all_project_details(request.user):
                continue
            projects = p.project_set.approved().filter(deadline=Project.CLOSED)
            if projects:
                closed_approved_projects.append((p.community, projects))
            projects = p.project_set.approved().filter(deadline=Project.ONTIME)
            if projects:
                ontime_approved_projects.append((p.community, p.interns_funded(), projects))
            projects = p.project_set.approved().filter(deadline=Project.LATE)
            if projects:
                late_approved_projects.append((p.community, p.interns_funded(), projects))

    return render(request, 'home/round_page_with_communities.html',
            {
            'current_round' : current_round,
            'previous_round' : previous_round,
            'closed_projects': closed_approved_projects,
            'ontime_projects': ontime_approved_projects,
            'late_projects': late_approved_projects,
            'example_skill': example_skill,
            'role': role,
            },
            )

# Call for communities, mentors, and volunteers page
#
# This is complex, so class-based views don't help us here.
#
# We want to display four sections:
#  * Blurb about what Outreachy is
#  * Timeline for the round
#  * Communities that are participating and are open to mentors and volunteers
#  * Communities that have participated and need to be claimed by coordinators
#
# We need to end up with:
#  * The most current round (by round number)
#  * The communities participating in the current round (which have their CFP open)
#  * The communities which aren't participating in the current round
#
# We need to do some database calls in order to get this info:
#  * Grab all the rounds, sort by round number (descending), hand us back one round
#  * For the current round, grab all Participations (communities participating)
#  * Grab all the communities
#
# To get the communities which aren't participating:
#  * Make a set of the community IDs from the communities
#    participating in the current round (participating IDs)
#  * Walk through all communities, seeing if the community ID is
#    in participating IDs.
#    * If so, put it in a participating communities set
#    * If not, put it in a not participating communities set

def community_cfp_view(request):
    # Cheap trick for case-insensitive sorting: the slug is always lower-cased.
    all_communities = Community.objects.all().order_by('slug')
    approved_communities = []
    pending_communities = []
    rejected_communities = []
    not_participating_communities = []

    # The problem here is the CFP page serves four (or more) purposes:
    # - to provide mentors a way to submit new projects
    # - to provide coordinators a way to submit new communities
    # - to allow mentors to sign up to co-mentor a project
    # - to allow mentors a way to edit their projects
    #
    # So, we close down the page after the interns are announced,
    # when (hopefully) all mentors have signed up to co-mentor.
    # Mentors can still be sent a manual link to sign up to co-mentor after that date,
    # but their community page just won't show their project.

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        previous_round = RoundPage.objects.filter(
            internstarts__lte=today,
        ).latest('internstarts')
    except RoundPage.DoesNotExist:
        previous_round = None

    try:
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            internstarts__gt=today,
        )
    except RoundPage.DoesNotExist:
        current_round = None
        not_participating_communities = all_communities.filter(
            participation__approval_status=ApprovalStatus.APPROVED,
        ).distinct()
    else:
        # No exception caught, so we have a current_round

        # Now grab the community IDs of all communities participating in the current round
        # https://docs.djangoproject.com/en/1.11/topics/db/queries/#following-relationships-backward
        # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values-list
        # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values
        participating_communities = {
                p.community_id: p
                for p in current_round.participation_set.all()
                }
        for c in all_communities:
            participation_info = participating_communities.get(c.id)
            if participation_info is not None:
                if participation_info.approval_status == ApprovalStatus.PENDING:
                    pending_communities.append(c)
                elif participation_info.approval_status == ApprovalStatus.APPROVED:
                    approved_communities.append(c)
                else: # either withdrawn or rejected
                    rejected_communities.append(c)
            else:
                not_participating_communities.append(c)

    # See https://docs.djangoproject.com/en/1.11/topics/http/shortcuts/
    return render(request, 'home/community_cfp.html',
            {
            'current_round' : current_round,
            'previous_round' : previous_round,
            'pending_communities': pending_communities,
            'approved_communities': approved_communities,
            'rejected_communities': rejected_communities,
            'not_participating_communities': not_participating_communities,
            },
            )

# This is the page for volunteers, mentors, and coordinators.
# It's a read-only page that displays information about the community,
# what projects are accepted, and how volunteers can help.
# If the community isn't participating in this round, the page displays
# instructions for being notified or signing the community up to participate.
def community_read_only_view(request, community_slug):
    community = get_object_or_404(Community, slug=community_slug)

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    participation_info = None

    try:
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            # If the application period is closed, don't show projects from the current round
            appslate__gt=today,
        )
        previous_round = None
    except RoundPage.DoesNotExist:
        current_round = None
        try:
            previous_round = community.rounds.filter(
                appslate__lte=today,
                participation__approval_status=ApprovalStatus.APPROVED,
            ).latest('internstarts')
        except RoundPage.DoesNotExist:
            previous_round = None
    else:
        # Try to see if this community is participating in the current round
        # and get the Participation object if so.
        try:
            participation_info = community.participation_set.get(participating_round=current_round)
        except Participation.DoesNotExist:
            pass

    coordinator = None
    notification = None
    mentors_pending_projects = ()
    if request.user.is_authenticated:
        try:
            # Although the current user is authenticated, don't assume
            # that they have a Comrade instance. Instead check that the
            # approval's coordinator is attached to a User that matches
            # this one.
            coordinator = community.coordinatorapproval_set.get(coordinator__account=request.user)
        except CoordinatorApproval.DoesNotExist:
            pass
        try:
            notification = community.notification_set.get(comrade__account=request.user)
        except Notification.DoesNotExist:
            pass

        if participation_info is not None and participation_info.approval_status in (ApprovalStatus.PENDING, ApprovalStatus.APPROVED):
            try:
                mentors_pending_projects = request.user.comrade.get_mentored_projects().pending().filter(
                    project_round=participation_info,
                )
            except Comrade.DoesNotExist:
                pass

    return render(request, 'home/community_read_only.html', {
        'current_round' : current_round,
        'previous_round' : previous_round,
        'community': community,
        'coordinator': coordinator,
        'notification': notification,
        'mentors_pending_projects': mentors_pending_projects,
        'participation_info': participation_info,
    })

# A Comrade wants to sign up to be notified when a community coordinator
# says this community is participating in a new round
class CommunityNotificationUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    fields = []

    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        try:
            return Notification.objects.get(comrade=self.request.user.comrade, community=community)
        except Notification.DoesNotExist:
            return Notification(comrade=self.request.user.comrade, community=community)

    def get_success_url(self):
        return self.object.community.get_preview_url()

def community_landing_view(request, round_slug, community_slug):
    # Try to see if this community is participating in that round
    # and if so, get the Participation object and related objects.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community', 'participating_round'),
            community__slug=community_slug,
            participating_round__slug=round_slug,
            )
    projects = participation_info.project_set.approved()
    ontime_projects = [p for p in projects if p.deadline == Project.ONTIME]
    late_projects = [p for p in projects if p.deadline == Project.LATE]
    closed_projects = [p for p in projects if p.deadline == Project.CLOSED]
    example_skill = ProjectSkill
    current_round = participation_info.participating_round

    role = Role(request.user, current_round)

    approved_coordinator_list = CoordinatorApproval.objects.none()
    if request.user.is_authenticated:
        approved_coordinator_list = participation_info.community.coordinatorapproval_set.approved()

    approved_to_see_all_project_details = participation_info.approved_to_see_all_project_details(request.user)

    mentors_pending_projects = Project.objects.none()
    approved_coordinator = False
    if request.user.is_authenticated:
        # If a mentor has submitted a project, they should be able to see all
        # their project details and have the link to edit the project, even if
        # the community is pending or the project isn't approved.
        try:
            # XXX: Despite the name, this is not limited to pending projects. Should it be?
            mentors_pending_projects = request.user.comrade.get_mentored_projects().filter(
                project_round=participation_info,
            )
        except Comrade.DoesNotExist:
            pass

        approved_coordinator = participation_info.community.is_coordinator(request.user)

    return render(request, 'home/community_landing.html',
            {
            'participation_info': participation_info,
            'ontime_projects': ontime_projects,
            'late_projects': late_projects,
            'closed_projects': closed_projects,
            'role': role,
            # TODO: make the template get these off the participation_info instead of passing them in the context
            'current_round' : current_round,
            'community': participation_info.community,
            'approved_coordinator_list': approved_coordinator_list,
            'approved_to_see_all_project_details': approved_to_see_all_project_details,
            'mentors_pending_projects': mentors_pending_projects,
            'approved_coordinator': approved_coordinator,
            'example_skill': example_skill,
            },
            )

class CommunityCreate(LoginRequiredMixin, ComradeRequiredMixin, CreateView):
    model = NewCommunity
    fields = ['name',
            'approved_license',
            'no_proprietary_software',
            'approved_advertising',
            'community_size', 'longevity', 'participating_orgs',
            'description',
            'long_description', 'tutorial', 'website',
            'goverance', 'code_of_conduct', 'cla', 'dco',
            'unapproved_license_description',
            'proprietary_software_description',
            'unapproved_advertising_description',
            ]

    def get_form(self):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        try:
            self.current_round = RoundPage.objects.filter(
                lateorgs__gt=today,
            ).earliest('lateorgs')
        except RoundPage.DoesNotExist:
            raise PermissionDenied("There is no round you can participate in right now.")
        return super(CommunityCreate, self).get_form()

    # We have to over-ride this method because we need to
    # create a community's slug from its name.
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.slug = slugify(self.object.name)[:self.object._meta.get_field('slug').max_length]
        self.object.save()

        # Whoever created this community is automatically approved as a
        # coordinator for it, even though the community itself isn't
        # approved yet.
        CoordinatorApproval.objects.create(
                coordinator=self.request.user.comrade,
                community=self.object,
                approval_status=ApprovalStatus.APPROVED)

        # When a new community is created, immediately redirect the
        # coordinator to gather information about their participation in
        # this round. The Participation object doesn't have to be saved
        # to the database yet; that'll happen when they submit it in the
        # next step.
        return redirect(Participation(
            community=self.object,
            participating_round=self.current_round,
        ).get_action_url('submit'))

class CommunityUpdate(LoginRequiredMixin, UpdateView):
    model = Community
    slug_url_kwarg = 'community_slug'
    fields = ['name', 'description', 'long_description', 'website', 'tutorial']

    def get_object(self):
        community = super(CommunityUpdate, self).get_object()
        if not community.is_coordinator(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

    def get_success_url(self):
        return self.object.get_preview_url()

class SponsorshipInlineFormSet(BaseInlineFormSet):
    def get_queryset(self):
        qs = super(SponsorshipInlineFormSet, self).get_queryset()
        return qs.filter(coordinator_can_update=True)

    def save_new(self, form, commit=True):
        # Ensure that new objects created by this form will still be
        # editable with it later.
        form.instance.coordinator_can_update = True
        return super(SponsorshipInlineFormSet, self).save_new(form, commit)

class ParticipationAction(ApprovalStatusAction):
    form_class = inlineformset_factory(Participation, Sponsorship,
            formset=SponsorshipInlineFormSet,
            fields='__all__', exclude=['coordinator_can_update'])

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])
        participating_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])
        try:
            return Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
        except Participation.DoesNotExist:
            return Participation(
                    community=community,
                    participating_round=participating_round)

    def get_context_data(self, **kwargs):
        context = super(ParticipationAction, self).get_context_data(**kwargs)
        context['readonly_sponsorships'] = self.object.sponsorship_set.filter(coordinator_can_update=False)
        return context

    def save_form(self, form):
        # We might be newly-creating the Participation or changing its
        # approval_status even though the form the user sees has no
        # fields off this object itself, so make sure to save it first
        # so it gets assigned a primary key.
        self.object.save()

        # InlineFormSet's save method returns the list of created or
        # changed Sponsorship objects, not the parent Participation.
        form.save()

        # Saving this form doesn't change which object is current.
        return self.object

    def notify(self):
        if self.prior_status == self.target_status:
            return

        email.approval_status_changed(self.object, self.request)

        if self.target_status == ApprovalStatus.PENDING:
            for notification in self.object.community.notification_set.all():
                email.notify_mentor(self.object, notification, self.request)
                notification.delete()

# This view is for mentors and coordinators to review project information and approve it
def project_read_only_view(request, round_slug, community_slug, project_slug):
    project = get_object_or_404(
            Project.objects.select_related('project_round__participating_round', 'project_round__community'),
            slug=project_slug,
            project_round__participating_round__slug=round_slug,
            project_round__community__slug=community_slug,
            )

    approved_mentors = project.mentorapproval_set.approved()
    unapproved_mentors = project.mentorapproval_set.filter(approval_status__in=(ApprovalStatus.PENDING, ApprovalStatus.REJECTED))

    mentor_request = None
    coordinator = None
    if request.user.is_authenticated:
        # For both of the following queries, although the current user
        # is authenticated, don't assume that they have a Comrade
        # instance. Instead check that the approval is attached to a
        # User that matches this one.

        try:
            # Grab the current user's mentor request regardless of its
            # status so we can tell them what their status is.
            mentor_request = project.mentorapproval_set.get(mentor__account=request.user)
        except MentorApproval.DoesNotExist:
            pass

        try:
            # Grab the current user's coordinator request for the
            # community this project is part of, but only if they've
            # been approved, because otherwise we don't treat them any
            # differently than anyone else.
            coordinator = project.project_round.community.coordinatorapproval_set.approved().get(coordinator__account=request.user)
        except CoordinatorApproval.DoesNotExist:
            pass

    return render(request, 'home/project_read_only.html',
            {
            'current_round': project.project_round.participating_round,
            'community': project.project_round.community,
            'project' : project,
            'approved_mentors': approved_mentors,
            'unapproved_mentors': unapproved_mentors,
            'mentor_request': mentor_request,
            'coordinator': coordinator,
            },
            )

class CoordinatorApprovalAction(ApprovalStatusAction):
    # We don't collect any information about coordinators beyond what's
    # in the Comrade model already.
    fields = []

    def get_object(self):
        community = get_object_or_404(Community, slug=self.kwargs['community_slug'])

        username = self.kwargs.get('username')
        if username:
            comrade = get_object_or_404(Comrade, account__username=username)
        else:
            comrade = self.request.user.comrade

        try:
            return CoordinatorApproval.objects.get(coordinator=comrade, community=community)
        except CoordinatorApproval.DoesNotExist:
            return CoordinatorApproval(coordinator=comrade, community=community)

    def get_success_url(self):
        if self.kwargs['action'] == 'submit':
            # There's nothing useful to see on the coordinator preview
            # page, so go to the community preview after submit instead.
            return self.object.community.get_preview_url()

        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status != self.target_status:
            email.approval_status_changed(self.object, self.request)

class MentorApprovalAction(ApprovalStatusAction):
    fields = [
            'instructions_read',
            'understands_intern_time_commitment',
            'understands_applicant_time_commitment',
            'understands_mentor_contract',
            'mentored_before',
            'mentorship_style',
            'longevity',
            'mentor_foss_contributions',
            'communication_channel_username',
            ]

    def get_object(self):
        project = get_object_or_404(Project,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'],
                slug=self.kwargs['project_slug'])

        username = self.kwargs.get('username')
        if username:
            mentor = get_object_or_404(Comrade, account__username=username)
        else:
            mentor = self.request.user.comrade

        try:
            return MentorApproval.objects.get(mentor=mentor, project=project)
        except MentorApproval.DoesNotExist:
            return MentorApproval(mentor=mentor, project=project)

    def get_success_url(self):
        # BaseProjectEditPage doesn't allow people who aren't
        # "submitters" for the project to edit skills/channels. So
        # we want initial project submission to go
        #   1. 'project-action'
        #   2. 'mentorapproval-action'
        #   3. 'project-skills-edit'
        #   4. 'communication-channels-edit'
        # but if this is a co-mentor signup the co-mentor can't follow
        # that route because they haven't been approved to edit the
        # project yet when they first sign up.
        if self.kwargs['action'] == 'submit' and self.object.project.is_submitter(self.request.user):
            return reverse('project-skills-edit', kwargs={
                'round_slug': self.object.project.project_round.participating_round.slug,
                'community_slug': self.object.project.project_round.community.slug,
                'project_slug': self.object.project.slug,
                })

        return self.object.project.get_preview_url()

    def notify(self):
        if self.prior_status != self.target_status:
            email.approval_status_changed(self.object, self.request)
            if self.target_status == MentorApproval.APPROVED:
                interns = self.object.project.get_interns()
                for i in interns:
                    if i.funding_source != InternSelection.NOT_FUNDED:
                        email.co_mentor_intern_selection_notification(i, self.request)

class ProjectAction(ApprovalStatusAction):
    fields = ['approved_license', 'no_proprietary_software', 'longevity', 'community_size', 'short_title', 'long_description', 'minimum_system_requirements', 'contribution_tasks', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'intern_tasks', 'intern_benefits', 'community_benefits', 'unapproved_license_description', 'proprietary_software_description', 'deadline', 'needs_more_applicants', ]

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    def get_object(self):
        participation = get_object_or_404(Participation,
                    community__slug=self.kwargs['community_slug'],
                    participating_round__slug=self.kwargs['round_slug'])

        project_slug = self.kwargs.get('project_slug')
        if project_slug:
            return get_object_or_404(Project,
                    project_round=participation,
                    slug=project_slug)
        else:
            return Project(project_round=participation)

    def save_form(self, form):
        project = form.save(commit=False)

        if not project.slug:
            project.slug = slugify(project.short_title)[:project._meta.get_field('slug').max_length]

        project.save()
        return project

    def get_success_url(self):
        if not self.kwargs.get('project_slug'):
            # If this is a new Project, associate an approved mentor with it
            mentor = MentorApproval.objects.create(
                    mentor=self.request.user.comrade,
                    project=self.object,
                    approval_status=ApprovalStatus.APPROVED)
            return mentor.get_action_url('submit', self.request.user)
        elif self.kwargs['action'] == 'submit':
            return reverse('project-skills-edit', kwargs={
                'round_slug': self.object.project_round.participating_round.slug,
                'community_slug': self.object.project_round.community.slug,
                'project_slug': self.object.slug,
                })
        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status == self.target_status:
            return

        email.approval_status_changed(self.object, self.request)

        if self.target_status == ApprovalStatus.PENDING:
            if not self.object.approved_license or not self.object.no_proprietary_software:
                email.project_nonfree_warning(self.object, self.request)

class BaseProjectEditPage(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    def get_object(self):
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'])
        if not project.is_submitter(self.request.user):
            raise PermissionDenied("You are not an approved mentor for this project")
        # Only allow adding new project communication channels or skills
        # for approved projects after the deadline has passed.
        deadline = project.submission_and_approval_deadline()
        if project.approval_status != ApprovalStatus.APPROVED and has_deadline_passed(deadline):
            raise PermissionDenied("The project submission and approval deadline ({date}) has passed. Please sign up for the announcement mailing list for a call for mentors for the next Outreachy internship round. https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce".format(date=deadline))
        return project

    def get_success_url(self):
        return reverse(self.next_view, kwargs=self.kwargs)

class ProjectSkillsEditPage(BaseProjectEditPage):
    template_name_suffix = '_skills_form'
    form_class = inlineformset_factory(Project, ProjectSkill, fields='__all__')
    next_view = 'communication-channels-edit'

class CommunicationChannelsEditPage(BaseProjectEditPage):
    template_name_suffix = '_channels_form'
    form_class = inlineformset_factory(Project, CommunicationChannel, fields='__all__')
    next_view = 'project-read-only'

class MentorApprovalPreview(Preview):
    def get_object(self):
        return get_object_or_404(
                MentorApproval,
                project__slug=self.kwargs['project_slug'],
                project__project_round__participating_round__slug=self.kwargs['round_slug'],
                project__project_round__community__slug=self.kwargs['community_slug'],
                mentor__account__username=self.kwargs['username'])

class CoordinatorApprovalPreview(Preview):
    def get_object(self):
        return get_object_or_404(
                CoordinatorApproval,
                community__slug=self.kwargs['community_slug'],
                coordinator__account__username=self.kwargs['username'])

class SendEmailView(LoginRequiredMixin, ComradeRequiredMixin, BaseEmailBackend, TemplateView):
    template_name = 'home/send_email_preview.html'

    def generate_messages(self, current_round, connection):
        """
        Subclasses must implement this function to generate the desired emails,
        and must pass the connection argument on to the final send_mail or
        send_messages calls.
        """
        pass

    def get_round(self):
        return get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

    def get_context_data(self, **kwargs):
        """
        Use this view's BaseEmailBackend implementation to do a dry-run of
        sending the generated messages, and return a preview of the messages
        that would be sent.
        """
        self.messages = []
        self.generate_messages(current_round=self.get_round(), connection=self)
        context = super(SendEmailView, self).get_context_data(**kwargs)
        context['messages'] = self.messages
        return context

    def send_messages(self, messages):
        """
        Implementation of BaseEmailBackend that just saves the generated
        messages on self, so get_context_data can dig them back out again.
        """
        self.messages.extend(messages)
        return len(messages)

    def post(self, request, *args, **kwargs):
        """
        Use the real email backend to send the generated messages.
        """
        with mail.get_connection() as connection:
            self.generate_messages(current_round=self.get_round(), connection=connection)
        return redirect(reverse('dashboard'))

class MentorCheckDeadlinesReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        projects = Project.objects.filter(
                approval_status__in=[Project.APPROVED, Project.PENDING],
                project_round__participating_round=current_round)
        for p in projects:
            email.project_applicant_review(p, self.request, connection=connection)

def get_open_approved_projects(current_round):
    if not current_round.has_ontime_application_deadline_passed():
        return Project.objects.filter(
                project_round__participating_round=current_round).all().approved()
    elif not current_round.has_late_application_deadline_passed():
        return Project.objects.filter(
                deadline=Project.LATE,
                project_round__participating_round=current_round).all().approved()
    return ()

def get_closed_approved_projects(current_round):
    if current_round.has_ontime_application_deadline_passed():
        return Project.objects.filter(
                project_round__participating_round=current_round,
                deadline__in=[Project.ONTIME, Project.CLOSED]).all().approved()
    elif current_round.has_late_application_deadline_passed():
        return Project.objects.filter(
                deadline=Project.LATE,
                project_round__participating_round=current_round).all().approved()
    return ()

class MentorApplicationDeadlinesReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        projects = get_open_approved_projects(current_round)
        for p in projects:
            email.mentor_application_deadline_reminder(p, self.request, connection=connection)

class MentorInternSelectionReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        projects = get_closed_approved_projects(current_round)
        for p in projects:
            email.mentor_intern_selection_reminder(p, self.request, connection=connection)

class CoordinatorInternSelectionReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        participations = Participation.objects.filter(
                participating_round=current_round,
                approval_status=Participation.APPROVED)
        for p in participations:
            email.coordinator_intern_selection_reminder(p, self.request, connection=connection)

class ApplicantsDeadlinesReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        late_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.LATE).order_by('project_round__community__name')
        promoted_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.ONTIME,
                needs_more_applicants=True).order_by('project_round__community__name')
        closed_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.CLOSED).order_by('project_round__community__name')
        email.applicant_deadline_reminder(late_projects, promoted_projects, closed_projects, current_round, self.request, connection=connection)

def get_contributors_with_upcoming_deadlines(current_round):
    ontime_deadline = current_round.appsclose
    late_deadline = current_round.appslate
    if not has_deadline_passed(ontime_deadline):
        return Comrade.objects.filter(
                applicantapproval__application_round=current_round,
                applicantapproval__approval_status=ApprovalStatus.APPROVED,
                applicantapproval__contribution__isnull=False).distinct()
    if not has_deadline_passed(late_deadline):
        return Comrade.objects.filter(
                applicantapproval__application_round=current_round,
                applicantapproval__approval_status=ApprovalStatus.APPROVED,
                applicantapproval__contribution__project__deadline=Project.LATE).distinct()
    return []

class ContributorsApplicationPeriodEndedReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        contributors = Comrade.objects.filter(
                applicantapproval__application_round=current_round,
                applicantapproval__approval_status=ApprovalStatus.APPROVED,
                applicantapproval__contribution__isnull=False).distinct()

        for c in contributors:
            email.contributor_application_period_ended(
                    c,
                    current_round,
                    self.request,
                    connection=connection)

class ContributorsDeadlinesReminder(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        contributors = get_contributors_with_upcoming_deadlines(current_round)

        for c in contributors:
            email.contributor_deadline_reminder(
                    c,
                    current_round,
                    self.request,
                    connection=connection)

class ProjectContributions(LoginRequiredMixin, ComradeRequiredMixin, EligibleApplicantRequiredMixin, TemplateView):
    template_name = 'home/project_contributions.html'

    def get_context_data(self, **kwargs):
        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        current_round = project.project_round.participating_round
        role = Role(self.request.user, current_round)

        # Note that there's no reason to ever keep a past applicant from
        # looking at their old contributions.

        applicant = role.application
        if applicant is None or not applicant.is_approved():
            raise Http404("No approved initial application in this round.")

        contributions = applicant.contribution_set.filter(
                project=project)
        try:
            final_application = applicant.finalapplication_set.get(
                    project=project)
        except FinalApplication.DoesNotExist:
            final_application = None

        context = super(ProjectContributions, self).get_context_data(**kwargs)
        context.update({
            'current_round' : current_round,
            'community': project.project_round.community,
            'project': project,
            'role': role,
            'contributions': contributions,
            'final_application': final_application,
            })
        return context

# Only submit one contribution at a time
class ContributionUpdate(LoginRequiredMixin, ComradeRequiredMixin, EligibleApplicantRequiredMixin, UpdateView):
    fields = [
            'date_started',
            'date_merged',
            'url',
            'description',
            ]

    def get_object(self):
        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        current_round = project.project_round.participating_round

        applicant = get_object_or_404(ApplicantApproval,
                applicant=self.request.user.comrade,
                application_round=current_round)
        try:
            application = FinalApplication.objects.get(
                    applicant=applicant,
                    project=project)
        except FinalApplication.DoesNotExist:
            application = None

        if not current_round.has_application_period_started():
            raise PermissionDenied("You cannot record a contribution until the Outreachy application period opens.")

        if project.has_application_deadline_passed() and application == None:
            raise PermissionDenied("Editing or recording new contributions is closed at this time to applicants who have not created a final application.")

        if current_round.has_intern_announcement_deadline_passed():
            raise PermissionDenied("Editing or recording new contributions is closed at this time.")

        if 'contribution_slug' not in self.kwargs:
            return Contribution(applicant=applicant, project=project)
        return get_object_or_404(Contribution,
                applicant=applicant,
                project=project,
                pk=self.kwargs['contribution_slug'])

    def get_success_url(self):
        return reverse('contributions', kwargs={
            'round_slug': self.object.project.project_round.participating_round.slug,
            'community_slug': self.object.project.project_round.community.slug,
            'project_slug': self.object.project.slug,
            })

class FinalApplicationRate(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=kwargs['community_slug'],
                project_round__participating_round__slug=kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        # Only allow approved mentors to rank applicants
        approved_mentors = project.get_approved_mentors()
        if request.user.comrade not in [m.mentor for m in approved_mentors]:
            raise PermissionDenied("You are not an approved mentor for this project.")

        current_round = project.project_round.participating_round

        if not current_round.has_application_period_started():
            raise PermissionDenied("You cannot rate an applicant until the Outreachy application period opens.")

        if current_round.has_last_day_to_add_intern_passed():
            raise PermissionDenied("Outreachy interns cannot be rated at this time.")

        applicant = get_object_or_404(ApplicantApproval,
                applicant__account__username=kwargs['username'],
                application_round=current_round,
                approval_status=ApprovalStatus.APPROVED)

        application = get_object_or_404(FinalApplication, applicant=applicant, project=project)
        rating = kwargs['rating']
        if rating in [c[0] for c in application.RATING_CHOICES]:
            application.rating = kwargs['rating']
            application.save()

        return redirect(reverse('project-applicants', kwargs={
            'round_slug': kwargs['round_slug'],
            'community_slug': kwargs['community_slug'],
            'project_slug': project.slug,
            }) + "#rating")

class FinalApplicationAction(ApprovalStatusAction):
    fields = [
            'experience',
            'foss_experience',
            'relevant_projects',
            'applying_to_gsoc',
            'community_specific_questions',
            'timeline',
            ]

    def get_object(self):
        username = self.kwargs.get('username')
        if username:
            comrade = get_object_or_404(Comrade, account__username=username)
        else:
            comrade = self.request.user.comrade

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        current_round = project.project_round.participating_round

        if not current_round.has_application_period_started():
            raise PermissionDenied("You can't submit a final application until the Outreachy application period opens.")

        if project.has_application_deadline_passed():
            raise PermissionDenied("This project is closed to final applications.")

        applicant = get_object_or_404(ApplicantApproval,
                applicant=comrade,
                application_round=current_round)

        # Only allow eligible applicants to apply
        if not applicant.is_approved():
            raise PermissionDenied("You are not an eligible applicant or you have not filled out the eligibility check.")

        try:
            return FinalApplication.objects.get(applicant=applicant, project=project)
        except FinalApplication.DoesNotExist:
            return FinalApplication(applicant=applicant, project=project)

    def get_success_url(self):
        return reverse('contributions', kwargs={
            'round_slug': self.object.project.project_round.participating_round.slug,
            'community_slug': self.object.project.project_round.community.slug,
            'project_slug': self.object.project.slug,
            })

class ProjectApplicants(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/project_applicants.html'

    def get_context_data(self, **kwargs):
        # Make sure both the Community, Project, and mentor are approved
        # Note that accessing URL parameters like project_slug off kwargs only
        # works because this is a TemplateView. For the various kinds of
        # DetailViews, you have to use self.kwargs instead.
        project = get_object_or_404(Project,
                slug=kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=kwargs['community_slug'],
                project_round__participating_round__slug=kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        current_round = project.project_round.participating_round

        # Note that there's no reason to ever keep someone who was a
        # coordinator or mentor in a past round from looking at who applied in
        # that round.

        if not self.request.user.is_staff and not project.project_round.community.is_coordinator(self.request.user) and not project.project_round.participating_round.is_mentor(self.request.user):
            raise PermissionDenied("You are not an approved mentor for this project.")

        contributions = project.contribution_set.filter(
                applicant__approval_status=ApprovalStatus.APPROVED).order_by(
                "applicant__applicant__public_name", "date_started")
        internship_total_days = current_round.internends - current_round.internstarts
        try:
            mentor_approval = MentorApproval.objects.get(
                    project=project,
                    mentor=self.request.user.comrade,
                    approval_status=MentorApproval.APPROVED)
        except MentorApproval.DoesNotExist:
            mentor_approval = None

        context = super(ProjectApplicants, self).get_context_data(**kwargs)
        context.update({
            'current_round': current_round,
            'community': project.project_round.community,
            'project': project,
            'contributions': contributions,
            'internship_total_days': internship_total_days,
            'approved_mentor': project.is_submitter(self.request.user),
            'mentor_approval': mentor_approval,
            })
        return context

@login_required
def community_applicants(request, round_slug, community_slug):
    # Make sure both the Community and mentor are approved
    participation = get_object_or_404(Participation,
            community__slug=community_slug,
            participating_round__slug=round_slug,
            approval_status=ApprovalStatus.APPROVED)

    current_round = participation.participating_round

    # Note that there's no reason to ever keep someone who was a coordinator or
    # mentor in a past round from looking at who applied in that round.

    user_is_coordinator = participation.community.is_coordinator(request.user)
    user_is_staff = request.user.is_staff
    if not user_is_staff and not user_is_coordinator and not participation.is_mentor(request.user):
        raise PermissionDenied("You are not an approved mentor for this community.")

    return render(request, 'home/community_applicants.html', {
        'current_round': current_round,
        'community': participation.community,
        'participation': participation,
        'is_coordinator': user_is_coordinator,
        'is_staff': user_is_staff,
        })

def contribution_tips(request):
    try:
        current_round = get_current_round_for_initial_application()
    except PermissionDenied:
        current_round = None # don't display any eligibility prompts

    role = Role(request.user, current_round)

    return render(request, 'home/contribution_tips.html', {
        'current_round': current_round,
        'role': role,
        })

def eligibility_information(request):
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        # The most relevant dates come from the soonest round where internships
        # haven't started yet...
        current_round = RoundPage.objects.filter(
            internstarts__gt=today,
        ).earliest('internstarts')
    except RoundPage.DoesNotExist:
        try:
            # ...but if there aren't any, use the round that started most
            # recently, so people get some idea of what the timeline looks like
            # even when the next round isn't announced yet.
            current_round = RoundPage.objects.latest('internstarts')
        except RoundPage.DoesNotExist:
            raise Http404("No internship rounds configured yet!")

    return render(request, 'home/eligibility.html', {
        'current_round': current_round,
        })

class TrustedVolunteersListView(UserPassesTestMixin, ListView):
    template_name = 'home/trusted_volunteers.html'

    def get_queryset(self):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        # Find all mentors and coordinators who are active in any round that is
        # currently running (anywhere from pingnew to internends).
        # Mentors get annoyed if they're re-subscribed after the internship ends.
        return Comrade.objects.filter(
                models.Q(
                    mentorapproval__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__project__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__project__project_round__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__project__project_round__participating_round__pingnew__lte=today,
                    mentorapproval__project__project_round__participating_round__internends__gt=today,
                ) | models.Q(
                    coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    coordinatorapproval__community__participation__approval_status=ApprovalStatus.APPROVED,
                    coordinatorapproval__community__participation__participating_round__pingnew__lte=today,
                    coordinatorapproval__community__participation__participating_round__internends__gt=today,
                )
            ).order_by('public_name').distinct()

    def test_func(self):
        return self.request.user.is_staff

# Is this a current or past intern in good standing?
# This will return None if the internship hasn't been announced yet.
def intern_in_good_standing(user):
    if not user.is_authenticated:
        return None
    try:
        internship = InternSelection.objects.get(
                applicant__applicant__account = user,
                project__approval_status = ApprovalStatus.APPROVED,
                project__project_round__approval_status = ApprovalStatus.APPROVED,
                organizer_approved = True,
                in_good_standing = True,
                )
        if not internship.round().has_intern_announcement_deadline_passed():
            internship = None
    except InternSelection.DoesNotExist:
        internship = None
    return internship

@login_required
def intern_contract_export_view(request):
    internship = intern_in_good_standing(request.user)
    if not internship:
        raise PermissionDenied("You are not an Outreachy intern.")
    if not internship.intern_contract:
        raise PermissionDenied("You have not signed your Outreachy internship contract.")

    response = HttpResponse(internship.intern_contract.text, content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="intern-contract-' + internship.intern_contract.legal_name + '-' + internship.intern_contract.date_signed.strftime("%Y-%m-%d") + '.md"'
    return response

def generic_intern_contract_export_view(request):
    with open(path.join(settings.BASE_DIR, 'docs', 'intern-agreement.md')) as iafile:
        intern_agreement = iafile.read()
    response = HttpResponse(intern_agreement, content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="intern-contract-generic-unsigned.md"'
    return response

# Passed round_slug, community_slug, project_slug, applicant_username
# Even if someone resigns as a mentor, we still want to keep their signed mentor agreement
class MentorContractExport(LoginRequiredMixin, ComradeRequiredMixin, View):
    def get(self, request, round_slug, community_slug, project_slug, applicant_username):
        try:
            mentor_relationship = MentorRelationship.objects.get(
                    mentor__mentor=request.user.comrade,
                    intern_selection__project__slug=self.kwargs['project_slug'],
                    intern_selection__project__project_round__community__slug=self.kwargs['community_slug'],
                    intern_selection__project__project_round__participating_round__slug=self.kwargs['round_slug'],
                    intern_selection__applicant__applicant__account__username=self.kwargs['applicant_username'],
                    )
        except MentorRelationship.DoesNotExist:
            raise PermissionDenied("Cannot export mentor contract. You have not signed a contract for this internship.")
        response = HttpResponse(mentor_relationship.contract.text, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="mentor-contract-' + mentor_relationship.contract.legal_name + '-' + mentor_relationship.contract.date_signed.strftime("%Y-%m-%d") + '.md"'
        return response

def generic_mentor_contract_export_view(request):
    with open(path.join(settings.BASE_DIR, 'docs', 'mentor-agreement.md')) as mafile:
        mentor_agreement = mafile.read()
    response = HttpResponse(mentor_agreement, content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="mentor-contract-generic-unsigned.md"'
    return response

@login_required
@staff_member_required
def contract_export_view(request, round_slug):
    def export_comrade_with_contract(comrade, contract):
        return {
                'public name': comrade.public_name,
                'legal name': comrade.legal_name,
                'blog URL': comrade.blog_url,
                'email address': comrade.account.email,
                'contract signed by': contract.legal_name,
                'contract signed on': str(contract.date_signed),
                'contract signed from': contract.ip_address,
                'contract text': contract.text,
                }

    this_round = get_object_or_404(RoundPage,
            slug=round_slug)
    interns = this_round.get_approved_intern_selections().exclude(intern_contract=None)
    dictionary_list = []
    for sel in interns:
        intern_export = export_comrade_with_contract(sel.applicant.applicant,
                sel.intern_contract)
        intern_export['community'] = sel.community_name()
        intern_export['mentors'] = [
                export_comrade_with_contract(mr.mentor.mentor, mr.contract)
                for mr in sel.mentorrelationship_set.all()
                ]
        dictionary_list.append(intern_export)
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-contracts.json"'
    return response

class SignedContractForm(ModelForm):
    class Meta:
        model = SignedContract
        fields = ('legal_name',)

class FinalApplicationForm(ModelForm):
    class Meta:
        model = FinalApplication
        fields = ('rating',)

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating == FinalApplication.UNRATED:
            raise ValidationError("You must provide a rating for the selected applicant.")
        return rating


class InternSelectionForm(MultiModelForm):
    form_classes = {
            'rating': FinalApplicationForm,
            'contract': SignedContractForm,
            }

def set_project_and_applicant(self, current_round):
    self.project = get_object_or_404(Project,
            slug=self.kwargs['project_slug'],
            approval_status=ApprovalStatus.APPROVED,
            project_round__community__slug=self.kwargs['community_slug'],
            project_round__participating_round=current_round,
            project_round__approval_status=ApprovalStatus.APPROVED)
    self.applicant = get_object_or_404(ApplicantApproval,
            applicant__account__username=self.kwargs['applicant_username'],
            approval_status=ApplicantApproval.APPROVED,
            application_round=current_round)

# Passed round_slug, community_slug, project_slug, applicant_username
class InternSelectionUpdate(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, FormView):
    form_class = InternSelectionForm
    template_name = 'home/internselection_form.html'

    def get_form_kwargs(self):
        kwargs = super(InternSelectionUpdate, self).get_form_kwargs()

        current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

        if not current_round.has_application_period_started():
            raise PermissionDenied("You can't select an intern until the Outreachy application period opens.")

        set_project_and_applicant(self, current_round)
        application = get_object_or_404(FinalApplication,
                applicant=self.applicant,
                project=self.project)

        # Usually, we want mentors to only be able to select new interns
        # until the deadline. However, sometimes an Outreachy mentor
        # needs to stop participating in the middle of the internship.
        # This function is the path for them to sign up to co-mentor
        # (so that they can submit internship feedback).
        if current_round.has_last_day_to_add_intern_passed():
            try:
                intern_selection = InternSelection.objects.get(
                    applicant=self.applicant,
                    project=self.project,
                    )
            except InternSelection.DoesNotExist:
                raise PermissionDenied("Intern selection is closed for this round.")

        # Allow mentors to sign up to co-mentor, up until the internship ends
        if current_round.has_internship_ended():
                raise PermissionDenied("You cannot sign up to mentor after an internship has ended.")


        # Only allow approved mentors to select interns
        try:
            self.mentor_approval = MentorApproval.objects.get(
                    mentor=self.request.user.comrade,
                    project=self.project,
                    approval_status=MentorApproval.APPROVED)
        except MentorApproval.DoesNotExist:
            raise PermissionDenied("Only approved mentors can select an applicant as an intern")

        # Don't allow mentors to sign the contract twice
        if MentorRelationship.objects.filter(
                    mentor = self.mentor_approval,
                    intern_selection__applicant = self.applicant).exists():
            raise PermissionDenied("This intern has already been selected for this project. You cannot sign the mentor agreement twice.")

        with open(path.join(settings.BASE_DIR, 'docs', 'mentor-agreement.md')) as mafile:
            self.mentor_agreement = mafile.read()

        # We pass in all object instances that already exist,
        # and the form will create new object instances in memory that aren't referenced.
        kwargs.update(instance={
            'rating': application,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(InternSelectionUpdate, self).get_context_data(**kwargs)
        try:
            intern_selection = InternSelection.objects.get(
                applicant=self.applicant,
                project=self.project,
                )
        except InternSelection.DoesNotExist:
            intern_selection = None

        context['mentor_agreement_html'] = markdownify(self.mentor_agreement)
        context['project'] = self.project
        context['community'] = self.project.project_round.community
        context['applicant'] = self.applicant
        context['intern_selection'] = intern_selection
        context['current_round'] = self.project.project_round.participating_round
        return context

    def form_valid(self, form):
        form['rating'].save()
        # Fill in the date and IP address of the signed contract
        intern_selection, was_intern_selection_created = InternSelection.objects.get_or_create(
                applicant=self.applicant,
                project=self.project,
                intern_starts=self.project.project_round.participating_round.internstarts,
                initial_feedback_opens=self.project.project_round.participating_round.initialfeedback - timedelta(days=7),
                initial_feedback_due=self.project.project_round.participating_round.initialfeedback,
                midpoint_feedback_opens=self.project.project_round.participating_round.midfeedback - timedelta(days=7),
                midpoint_feedback_due=self.project.project_round.participating_round.midfeedback,
                intern_ends=self.project.project_round.participating_round.internends,
                )
        signed_contract = form['contract'].save(commit=False)
        signed_contract.date_signed = datetime.now(timezone.utc)
        signed_contract.ip_address = self.request.META.get('REMOTE_ADDR')
        signed_contract.text = self.mentor_agreement
        signed_contract.save()
        mentor_relationship = MentorRelationship(
                intern_selection=intern_selection,
                mentor=self.mentor_approval,
                contract=signed_contract).save()
        # If we just created this intern selection,
        # email all co-mentors and encourage them to sign the mentor agreement.
        if was_intern_selection_created:
            email.co_mentor_intern_selection_notification(intern_selection, self.request)
        # Send emails about any project conflicts
        email.intern_selection_conflict_notification(intern_selection, self.request)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('project-applicants', kwargs={
            'round_slug': self.kwargs['round_slug'],
            'community_slug': self.kwargs['community_slug'],
            'project_slug': self.kwargs['project_slug'],
            }) + "#rating"

# Passed round_slug, community_slug, project_slug, applicant_username
class InternRemoval(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, DeleteView):
    model = InternSelection
    template_name = 'home/intern_removal_form.html'

    def get_object(self):
        current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

        # If the internship is currently active,
        # then only Outreachy organizers should remove interns
        # by setting them not in good standing on the alums page.
        if current_round.is_internship_active():
            raise PermissionDenied("Only Outreachy organizers can remove an intern after the internship starts.")

        # Mentors shouldn't be able to delete interns after the internship ends.
        if current_round.has_internship_ended():
            raise PermissionDenied("Outreachy interns cannot be removed after the internship ends.")

        set_project_and_applicant(self, current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)
        self.mentor_relationships = self.intern_selection.mentorrelationship_set.all()

        # Only allow approved mentors to remove interns
        # Coordinators can set the funding to 'Not funded'
        # Organizers can set the InternSelection.organizer_approved to False
        try:
            self.mentor_approval = MentorApproval.objects.get(
                    mentor=self.request.user.comrade,
                    project=self.project,
                    approval_status=MentorApproval.APPROVED)
        except MentorApproval.DoesNotExist:
            raise PermissionDenied("Only approved mentors can select an applicant as an intern")
        return self.intern_selection

    def get_context_data(self, **kwargs):
        context = super(InternRemoval, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['community'] = self.project.project_round.community
        context['applicant'] = self.applicant
        context['current_round'] = self.project.project_round.participating_round
        return context

    # get_success_url is called before the object is deleted in DeleteView.delete()
    # so the objects are still in the database.
    def get_success_url(self):

        # Delete all the associated signed contracts
        # The MentorRelationships will be deleted automatically
        # However, if a mentor resigned from the internship,
        # the contract will still be around, and that's ok.
        for relationship in self.mentor_relationships:
            relationship.contract.delete()

        return reverse('project-applicants', kwargs={
            'round_slug': self.kwargs['round_slug'],
            'community_slug': self.kwargs['community_slug'],
            'project_slug': self.kwargs['project_slug'],
            }) + "#rating"

@login_required
def project_timeline(request, round_slug, community_slug, project_slug, applicant_username):
    intern_selection = get_object_or_404(InternSelection,
            applicant__applicant__account__username=applicant_username,
            project__slug=project_slug,
            project__project_round__community__slug=community_slug,
            project__project_round__participating_round__slug=round_slug)

    final_application = intern_selection.get_application()

    # Verify that this is either:
    # the intern,
    # staff,
    # an approved mentor for the project, or
    # an approved coordinator for the community.
    # The last two cases are covered by is_submitter()
    if not request.user.is_staff and not request.user == intern_selection.applicant.applicant.account and not intern_selection.is_submitter(request.user):
        raise PermissionDenied("You are not authorized to view this intern project timeline.")

    return render(request, 'home/intern_timeline.html', {
        'intern_selection': intern_selection,
        'project': intern_selection.project,
        'community': intern_selection.project.project_round.community,
        'current_round': intern_selection.project.project_round.participating_round,
        'final_application': final_application,
        })

# Passed round_slug, community_slug, project_slug, applicant_username
# Even if someone resigns as a mentor, we still want to keep their signed mentor agreement
class MentorResignation(LoginRequiredMixin, ComradeRequiredMixin, DeleteView):
    model = MentorRelationship
    template_name = 'home/mentor_resignation_form.html'

    def get_object(self):
        self.current_round = RoundPage.objects.get(slug=self.kwargs['round_slug'])
        if self.current_round.has_internship_ended():
            raise PermissionDenied("You cannot resign as a mentor from an internship from a past Outreachy round.")

        set_project_and_applicant(self, self.current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)

        # Only allow approved mentors to resign from the internship
        try:
            self.mentor_approval = MentorApproval.objects.get(
                    mentor=self.request.user.comrade,
                    project=self.project,
                    approval_status=MentorApproval.APPROVED)
        except MentorApproval.DoesNotExist:
            raise PermissionDenied("Only approved mentors can resign from an internship.")
        return get_object_or_404(self.intern_selection.mentorrelationship_set,
                mentor=self.mentor_approval)

    def get_context_data(self, **kwargs):
        context = super(MentorResignation, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['community'] = self.project.project_round.community
        context['applicant'] = self.applicant
        context['current_round'] = self.current_round
        return context

    def get_success_url(self):
        # Store the signed mentor contract for resigned mentors
        return reverse('project-applicants', kwargs={
            'round_slug': self.kwargs['round_slug'],
            'community_slug': self.kwargs['community_slug'],
            'project_slug': self.kwargs['project_slug'],
            }) + "#rating"

class InternFund(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = get_object_or_404(RoundPage, slug=kwargs['round_slug'])

        if not current_round.has_application_period_started():
            raise PermissionDenied("You cannot set a funding source for an Outreachy intern until the application period opens.")

        if current_round.has_last_day_to_add_intern_passed():
            raise PermissionDenied("Funding sources for Outreachy interns cannot be changed at this time.")

        set_project_and_applicant(self, current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)

        # Only allow approved coordinators and organizers to select intern funding
        user_is_coordinator = self.project.project_round.community.is_coordinator(request.user)
        user_is_staff = request.user.is_staff
        if not user_is_staff and not user_is_coordinator:
            raise PermissionDenied("Only approved coordinators and organizers can set intern funding sources.")

        funding = kwargs['funding']
        if funding in [c[0] for c in self.intern_selection.FUNDING_CHOICES]:
            if funding == InternSelection.ORG_FUNDED:
                # 'project_round' is the Participation (community and round)
                # Look for which are org-funded interns in this round for this community
                org_funded_intern_count = InternSelection.objects.filter(
                        project__project_round=self.intern_selection.project.project_round,
                        funding_source=InternSelection.ORG_FUNDED).count()
                if org_funded_intern_count + 1 > self.intern_selection.project.project_round.interns_funded():
                    raise PermissionDenied("You've selected more interns for organization funding than you have sponsored funds available. Please use your web browser back button and choose another funding source.")

            past_funding = self.intern_selection.funding_source
            self.intern_selection.funding_source = kwargs['funding']
            self.intern_selection.save()

            # If the coordinator or organizer is moving this intern from NOT_FUNDED
            # to any other state, send emails about any project conflicts
            if past_funding == InternSelection.NOT_FUNDED and funding != InternSelection.NOT_FUNDED:
                email.intern_selection_conflict_notification(self.intern_selection, self.request)

        return redirect(reverse('community-applicants', kwargs={
            'round_slug': kwargs['round_slug'],
            'community_slug': kwargs['community_slug'],
            }) + "#interns")

class InternApprove(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = get_object_or_404(RoundPage, slug=kwargs['round_slug'])

        if not current_round.has_application_period_started():
            raise PermissionDenied("You cannot approve an Outreachy intern until the application period opens.")

        if current_round.has_last_day_to_add_intern_passed():
            raise PermissionDenied("Approval status for Outreachy interns cannot be changed at this time.")

        set_project_and_applicant(self, current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)

        # Only allow approved organizers to approve interns
        if not request.user.is_staff:
            raise PermissionDenied("Only organizers can approve interns.")

        funding = kwargs['approval']
        if funding == "Approved":
            self.intern_selection.organizer_approved = True
        elif funding == "Rejected":
            self.intern_selection.organizer_approved = False
        elif funding == "Undecided":
            self.intern_selection.organizer_approved = None
        self.intern_selection.save()

        return redirect(reverse('dashboard') + "#intern-{project}-{applicant}".format(
            project=self.intern_selection.project.slug,
            applicant=self.intern_selection.applicant.applicant.pk))

class AlumStanding(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        # Only allow approved organizers to approve interns
        if not request.user.is_staff:
            raise PermissionDenied("Only organizers can approve interns.")

        username = kwargs['applicant_username']
        that_round = get_object_or_404(RoundPage,
                slug=kwargs['round_slug'])

        # FIXME - also need a method to hide AlumInfo
        set_project_and_applicant(self, that_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)

        standing = kwargs['standing']
        if kwargs['standing'] == "Good":
            self.intern_selection.in_good_standing = True
        elif kwargs['standing'] == "Failed":
            self.intern_selection.in_good_standing = False
        self.intern_selection.save()

        return redirect(reverse('alums'))

# Passed round_slug, community_slug, project_slug, (get applicant from request.user)
class InternAgreementSign(LoginRequiredMixin, ComradeRequiredMixin, CreateView):
    model = SignedContract
    template_name = 'home/internrelationship_form.html'
    fields = ('legal_name',)

    def set_project_and_intern_selection(self):
        self.current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])
        if not self.current_round.has_intern_announcement_deadline_passed():
            raise PermissionDenied("Intern agreements cannot be signed before the interns are announced.")

        # Since interns can't sign the contract twice, the only people who
        # could sign a contract for a past round are people who never signed it
        # when they were supposed to. If somehow that happens (it shouldn't!),
        # let's not limit which round an intern can sign a contract for.

        self.project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=self.current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)

        try:
            self.intern_selection = InternSelection.objects.get(
                applicant__applicant=self.request.user.comrade,
                funding_source__in=(InternSelection.ORG_FUNDED, InternSelection.GENERAL_FUNDED),
                organizer_approved=True,
                applicant__application_round=self.current_round
            )
        except InternSelection.DoesNotExist:
            raise PermissionDenied("You are not an intern in this round.")

        # Don't allow interns to sign the contract twice
        if self.intern_selection.intern_contract != None:
            raise PermissionDenied("You have already signed the intern agreement.")

        with open(path.join(settings.BASE_DIR, 'docs', 'intern-agreement.md')) as iafile:
            self.intern_agreement = iafile.read()


    def get_context_data(self, **kwargs):
        context = super(InternAgreementSign, self).get_context_data(**kwargs)

        self.set_project_and_intern_selection()

        context['intern_agreement_html'] = markdownify(self.intern_agreement)
        context['project'] = self.project
        context['community'] = self.project.project_round.community
        context['intern_selection'] = self.intern_selection
        context['applicant'] = self.intern_selection.applicant
        context['current_round'] = self.current_round
        return context

    def form_valid(self, form):
        self.set_project_and_intern_selection()

        intern_contract = form.save(commit=False)
        intern_contract.date_signed = datetime.now(timezone.utc)
        intern_contract.ip_address = self.request.META.get('REMOTE_ADDR')
        intern_contract.text = self.intern_agreement
        intern_contract.save()
        self.intern_selection.intern_contract = intern_contract
        self.intern_selection.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('dashboard')

def round_statistics(request, round_slug):
    current_round = RoundPage.objects.get(slug=round_slug)
    todays_date = datetime.now()
    return render(request, 'home/blog/round-statistics.html', {
        'current_round': current_round,
        'todays_date': todays_date,
        })

class InternNotification(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        interns = current_round.get_approved_intern_selections()

        for i in interns:
            email.notify_accepted_intern(i, self.request, connection=connection)

class InternWeek(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        template = 'home/email/internship-week-{}.txt'.format(self.kwargs['week'])
        interns = current_round.get_in_good_standing_intern_selections()

        for i in interns:
            email.biweekly_internship_email(i, self.request, template, connection=connection)

class InitialFeedbackInstructions(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_initial_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "initial", i.is_initial_feedback_on_intern_past_due(), connection=connection)

class InitialMentorFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(InitialMentorFeedback,
            fields=(
                'in_contact',
                'asking_questions',
                'active_in_public',
                'provided_onboarding',
                'checkin_frequency',
                'last_contact',
                'intern_response_time',
                'mentor_response_time',
                'payment_approved',
                'full_time_effort',
                'progress_report',
                'mentors_report',
                'request_extension',
                'extension_date',
                'request_termination',
                'termination_reason',
            ),
            field_classes = {
                'in_contact': RadioBooleanField,
                'asking_questions': RadioBooleanField,
                'active_in_public': RadioBooleanField,
                'provided_onboarding': RadioBooleanField,
                'full_time_effort': RadioBooleanField,
                'payment_approved': RadioBooleanField,
                'request_extension': RadioBooleanField,
                'request_termination': RadioBooleanField,
            },
        )

    def get_object(self):
        applicant = get_object_or_404(User, username=self.kwargs['username'])
        mentor_relationship = MentorRelationship.objects.filter(
            mentor__mentor__account=self.request.user,
            intern_selection__applicant__applicant__account=applicant,
        )

        if not mentor_relationship.exists():
            raise PermissionDenied("You are not a mentor for {}.".format(self.kwargs['username']))

        internship = intern_in_good_standing(applicant)
        if not internship:
            raise PermissionDenied("{} is not an intern in good standing".format(self.kwargs['username']))

        try:
            feedback = InitialMentorFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except InitialMentorFeedback.DoesNotExist:
            return InitialMentorFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class InitialInternFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(InitialInternFeedback,
            fields=(
                'in_contact',
                'asking_questions',
                'active_in_public',
                'provided_onboarding',
                'checkin_frequency',
                'last_contact',
                'intern_response_time',
                'mentor_response_time',
                'mentor_support',
                'hours_worked',
                'progress_report',
                ),
            field_classes = {
                'in_contact': RadioBooleanField,
                'asking_questions': RadioBooleanField,
                'active_in_public': RadioBooleanField,
                'provided_onboarding': RadioBooleanField,
                },
            )
    def get_object(self):
        internship = intern_in_good_standing(self.request.user)
        if not internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = InitialInternFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except InitialInternFeedback.DoesNotExist:
            return InitialInternFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

def export_feedback(feedback):
    return {
            'intern public name': feedback.intern_selection.applicant.applicant.public_name,
            'intern legal name': feedback.intern_selection.applicant.applicant.legal_name,
            'intern email address': feedback.intern_selection.applicant.applicant.account.email,
            'community': feedback.intern_selection.community_name(),
            'mentor public name': feedback.get_mentor_public_name(),
            'mentor legal name': feedback.get_mentor_legal_name(),
            'mentor email address': feedback.get_mentor_email(),
            'feedback submitted on': str(feedback.get_date_submitted()),
            'feedback submitted from': feedback.ip_address,
            'payment approved': feedback.payment_approved,
            'progress report': feedback.progress_report,
            'extension requested': feedback.request_extension,
            'extension date': str(feedback.extension_date),
            'termination requested': feedback.request_termination,
            'termination reason': feedback.termination_reason,
            }

@login_required
@staff_member_required
def initial_mentor_feedback_export_view(request, round_slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    interns = this_round.get_approved_intern_selections()
    dictionary_list = []
    for i in interns:
        try:
            dictionary_list.append(export_feedback(i.initialmentorfeedback))
        except InitialMentorFeedback.DoesNotExist:
            continue
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-initial-feedback.json"'
    return response

@login_required
@staff_member_required
def initial_feedback_summary(request, round_slug):
    current_round = RoundPage.objects.get(slug=round_slug)

    return render(request, 'home/initial_feedback.html',
            {
            'current_round' : current_round,
            },
            )

class MidpointFeedbackInstructions(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_midpoint_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "midpoint", i.is_midpoint_feedback_on_intern_past_due(), connection=connection)

class MidpointMentorFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(MidpointMentorFeedback,
            fields=(
                'intern_help_requests_frequency',
                'mentor_help_response_time',
                'last_contact',
                'intern_contribution_frequency',
                'mentor_review_response_time',
                'intern_contribution_revision_time',
                'payment_approved',
                'full_time_effort',
                'progress_report',
                'request_extension',
                'extension_date',
                'request_termination',
                'termination_reason',
            ),
            field_classes = {
                'in_contact': RadioBooleanField,
                'full_time_effort': RadioBooleanField,
                'payment_approved': RadioBooleanField,
                'request_extension': RadioBooleanField,
                'request_termination': RadioBooleanField,
            },
        )

    def get_object(self):
        applicant = get_object_or_404(User, username=self.kwargs['username'])
        mentor_relationship = MentorRelationship.objects.filter(
            mentor__mentor__account=self.request.user,
            intern_selection__applicant__applicant__account=applicant,
        )

        if not mentor_relationship.exists():
            raise PermissionDenied("You are not a mentor for {}.".format(self.kwargs['username']))

        internship = intern_in_good_standing(applicant)
        if not internship:
            raise PermissionDenied("{} is not an intern in good standing".format(self.kwargs['username']))

        try:
            feedback = MidpointMentorFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except MidpointMentorFeedback.DoesNotExist:
            return MidpointMentorFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class MidpointInternFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(MidpointInternFeedback,
            fields=(
                'intern_help_requests_frequency',
                'mentor_help_response_time',
                'intern_contribution_frequency',
                'mentor_review_response_time',
                'intern_contribution_revision_time',
                'last_contact',
                'mentor_support',
                'hours_worked',
                'progress_report',
                ),
            )

    def get_object(self):
        internship = intern_in_good_standing(self.request.user)
        if not internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = MidpointInternFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except MidpointInternFeedback.DoesNotExist:
            return MidpointInternFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

@login_required
@staff_member_required
def midpoint_mentor_feedback_export_view(request, round_slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    interns = this_round.get_approved_intern_selections()
    dictionary_list = []
    for i in interns:
        try:
            dictionary_list.append(export_feedback(i.midpointmentorfeedback))
        except MidpointMentorFeedback.DoesNotExist:
            continue
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-midpoint-feedback.json"'
    return response

@login_required
@staff_member_required
def midpoint_feedback_summary(request, round_slug):
    current_round = RoundPage.objects.get(slug=round_slug)

    return render(request, 'home/midpoint_feedback.html',
            {
            'current_round' : current_round,
            },
            )

class FinalFeedbackInstructions(SendEmailView):
    def generate_messages(self, current_round, connection):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")

        # Only get interns that are in good standing and
        # where a mentor or intern hasn't submitted feedback.
        interns = current_round.get_interns_with_open_final_feedback()

        for i in interns:
            email.feedback_email(i, self.request, "final", i.is_final_feedback_on_intern_past_due(), connection=connection)

class FinalMentorFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(FinalMentorFeedback,
            fields=(
                'intern_help_requests_frequency',
                'mentor_help_response_time',
                'last_contact',
                'intern_contribution_frequency',
                'mentor_review_response_time',
                'intern_contribution_revision_time',
                'payment_approved',
                'full_time_effort',
                'progress_report',
                'request_extension',
                'extension_date',
                'request_termination',
                'termination_reason',
                'mentoring_recommended',
                'blog_frequency',
                'blog_prompts_caused_writing',
                'blog_prompts_caused_overhead',
                'recommend_blog_prompts',
                'zulip_caused_intern_discussion',
                'zulip_caused_mentor_discussion',
                'recommend_zulip',
                'feedback_for_organizers',
            ),
            field_classes = {
                'in_contact': RadioBooleanField,
                'full_time_effort': RadioBooleanField,
                'payment_approved': RadioBooleanField,
                'request_extension': RadioBooleanField,
                'request_termination': RadioBooleanField,
            },
        )

    def get_object(self):
        applicant = get_object_or_404(User, username=self.kwargs['username'])
        mentor_relationship = MentorRelationship.objects.filter(
            mentor__mentor__account=self.request.user,
            intern_selection__applicant__applicant__account=applicant,
        )

        if not mentor_relationship.exists():
            raise PermissionDenied("You are not a mentor for {}.".format(self.kwargs['username']))

        internship = intern_in_good_standing(applicant)
        if not internship:
            raise PermissionDenied("{} is not an intern in good standing".format(self.kwargs['username']))

        try:
            feedback = FinalMentorFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except FinalMentorFeedback.DoesNotExist:
            return FinalMentorFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class FinalInternFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(FinalInternFeedback,
            fields=(
                'intern_help_requests_frequency',
                'mentor_help_response_time',
                'intern_contribution_frequency',
                'mentor_review_response_time',
                'intern_contribution_revision_time',
                'last_contact',
                'mentor_support',
                'hours_worked',
                'progress_report',
                'interning_recommended',
                'tech_industry_prep',
                'foss_confidence',
                'recommend_intern_chat',
                'chat_frequency',
                'blog_prompts_caused_writing',
                'blog_prompts_caused_overhead',
                'blog_frequency',
                'recommend_blog_prompts',
                'zulip_caused_intern_discussion',
                'zulip_caused_mentor_discussion',
                'recommend_zulip',
                'feedback_for_organizers',
                ),
            )

    def get_object(self):
        internship = intern_in_good_standing(self.request.user)
        if not internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = FinalInternFeedback.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except FinalInternFeedback.DoesNotExist:
            return FinalInternFeedback(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

@login_required
@staff_member_required
def final_mentor_feedback_export_view(request, round_slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    interns = this_round.get_approved_intern_selections()
    dictionary_list = []
    for i in interns:
        try:
            dictionary_list.append(export_feedback(i.finalmentorfeedback))
        except FinalMentorFeedback.DoesNotExist:
            continue
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-final-feedback.json"'
    return response

@login_required
@staff_member_required
def final_feedback_summary(request, round_slug):
    current_round = RoundPage.objects.get(slug=round_slug)

    return render(request, 'home/final_feedback.html',
            {
            'current_round' : current_round,
            },
            )

def alums_page(request):
    # Get all the older AlumInfo models (before we had round pages)
    pages = CohortPage.objects.all()
    old_cohorts = []
    for p in pages:
        old_cohorts.append((p.round_start, p.round_end,
            AlumInfo.objects.filter(page=p).order_by('community', 'name')))
    rounds = RoundPage.objects.all().order_by('-internstarts')
    rounds = [x for x in rounds if x.has_intern_announcement_deadline_passed() and x.get_approved_intern_selections() != None]
    return render(request, 'home/alums.html', {
        'old_cohorts': old_cohorts,
        'rounds': rounds,
        })

def privacy_policy(request):
    with open(path.join(settings.BASE_DIR, 'docs', 'privacy-policy.md')) as policy_file:
        policy = policy_file.read()
    return render(request, 'home/privacy_policy.html', {
        'privacy_policy': markdownify(policy),
        })

def survey_opt_out(request, survey_slug):
    signer = TimestampSigner()
    try:
        this_pk = signer.unsign(survey_slug)
    except BadSignature:
        raise PermissionDenied("Bad survey opt-out link.")

    try:
        survey_tracker = AlumSurveyTracker.objects.get(pk=this_pk)
    except AlumSurveyTracker.DoesNotExist:
        raise PermissionDenied("Bad survey opt-out link.")

    if survey_tracker.alumni_info != None:
        survey_tracker.alumni_info.survey_opt_out = True
        survey_tracker.alumni_info.save()
    elif survey_tracker.intern_info != None:
        survey_tracker.intern_info.survey_opt_out = True
        survey_tracker.intern_info.save()

    return render(request, 'home/survey_opt_out_confirmation.html')

class AlumSurveyUpdate(UpdateView):
    form_class = modelform_factory(AlumSurvey, exclude=(
        'survey_tracker',
        'survey_date',
        ),
        field_classes={
            'community_contact': RadioBooleanField,
        },
    )

    def get_object(self):
        # Decode the timestamped data:
        # - the PK of the AlumSurveyTracker
        #
        # If the timestamp is older than 1 month, display an error message.
        #
        # Figure out which model is not null (alumni_info or intern_info) to use.
        # See if we already have an AlumSurvey that points to this survey tracker.
        # If not, create it.
        signer = TimestampSigner()
        try:
            this_pk = signer.unsign(self.kwargs['survey_slug'], max_age=timedelta(days=30))
        except SignatureExpired:
            raise PermissionDenied("The survey link has expired.")
        except BadSignature:
            raise PermissionDenied("Bad survey link.")

        try:
            return AlumSurvey.objects.get(survey_tracker__pk=this_pk)
        except AlumSurvey.DoesNotExist:
            tracker = get_object_or_404(AlumSurveyTracker, pk=this_pk)
            return AlumSurvey(survey_tracker=tracker, survey_date=datetime.now())

    # No need to override get_context because we can get everything from
    # form.instance.survey_tracker

    def get_success_url(self):
        return reverse('longitudinal-survey-2018-completed')

class Survey2018Notification(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/survey_notification.html'

    def get_alums_and_opt_outs(self):
        alums = AlumInfo.objects.all()
        alums_opt_out = [p for p in alums if p.survey_opt_out == True]
        alums = [p for p in alums if p.survey_opt_out == False]

        # Only send the survey to interns who have completed their internship
        past_interns = InternSelection.objects.filter(organizer_approved=True,
                project__project_round__participating_round__internends__lte=date.today())
        past_interns_opt_out = [p for p in past_interns if p.survey_opt_out == True or p.project.project_round.participating_round.internends >= date.today()]
        past_interns = [p for p in past_interns if p.survey_opt_out == False and p.project.project_round.participating_round.internends >= date.today()]

        return alums, alums_opt_out, past_interns, past_interns_opt_out

    def get_context_data(self, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send survey emails.")

        alums, alums_opt_out, past_interns, past_interns_opt_out = self.get_alums_and_opt_outs()
        len_queued_surveys = AlumSurveyTracker.objects.filter(survey_date__isnull=True).count()

        context = super(Survey2018Notification, self).get_context_data(**kwargs)
        context.update({
            'alums': alums,
            'alums_opt_out': alums_opt_out,
            'past_interns': past_interns,
            'past_interns_opt_out': past_interns_opt_out,
            'len_queued_surveys': len_queued_surveys,
            })
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        alums, alums_opt_out, past_interns, past_interns_opt_out = self.get_alums_and_opt_outs()

        for a in alums:
            AlumSurveyTracker.objects.create(alumni_info=a)
        for p in past_interns:
            AlumSurveyTracker.objects.create(intern_info=i)
        return redirect(reverse('dashboard'))

@login_required
def applicant_review_summary(request, status):
    """
    For applicant reviewers and staff, show the status of applications that
    have the specified approval status.
    """
    current_round = get_current_round_for_initial_application()

    if not request.user.is_staff and not current_round.is_reviewer(request.user):
        raise PermissionDenied("You are not authorized to review applications.")

    applications = ApplicantApproval.objects.filter(
        application_round=current_round,
        approval_status=status,
    ).order_by('pk')

    if status == ApprovalStatus.PENDING:
        context_name = 'pending_applications'
    elif status == ApprovalStatus.REJECTED:
        context_name = 'rejected_applications'
    elif status == ApprovalStatus.APPROVED:
        context_name = 'approved_applications'

    return render(request, 'home/applicant_review_summary.html', {
        context_name: applications,
    })

# Passed action, applicant_username
class ApplicantApprovalUpdate(ApprovalStatusAction):
    model = ApplicantApproval

    def get_object(self):
        current_round = get_current_round_for_initial_application()
        return get_object_or_404(ApplicantApproval,
                applicant__account__username=self.kwargs['applicant_username'],
                application_round=current_round)

    def notify(self):
        if self.prior_status != self.target_status:
            # email applicant about their change in status
            email.approval_status_changed(self.object, self.request,
                from_email=email.applicant_help)

    def get_success_url(self):
        return reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            })

class DeleteApplication(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        # Only allow staff to delete initial applications
        if not request.user.is_staff:
            raise PermissionDenied("Only Outreachy organizers can delete initial applications.")

        current_round = get_current_round_for_initial_application()
        application = get_object_or_404(ApplicantApproval,
                applicant__account__username=self.kwargs['applicant_username'],
                application_round=current_round)
        application.delete()

        # We need to delete both pending and rejected applications,
        # so I'm not sure which to redirect to.
        return redirect(reverse('dashboard'))

class NotifyEssayNeedsUpdating(LoginRequiredMixin, ComradeRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        current_round = get_current_round_for_initial_application()
        # Allow staff to ask applicants to revise their essays
        if not request.user.is_staff:
            raise PermissionDenied("Only Outreachy organizers can ask applicants to revise their essays.")

        essay = get_object_or_404(BarriersToParticipation,
                applicant__application_round=current_round,
                applicant__applicant__account__username=self.kwargs['applicant_username'],
                )
        essay.applicant_should_update = True
        essay.save()
        # Notify applicant their essay needs review
        email.applicant_essay_needs_updated(essay.applicant.applicant, request)
        return redirect(reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            }))

class BarriersToParticipationUpdate(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    model = BarriersToParticipation

    fields = [
            'lacking_representation',
            'systemic_bias',
            'employment_bias',
            'barriers_to_contribution',
            ]

    def get_object(self):
        current_round = get_current_round_for_initial_application()
        # Only allow applicants to revise their own essays
        if self.request.user.comrade.account.username != self.kwargs['applicant_username']:
            raise PermissionDenied('You can only edit your own essay.')
        essay = get_object_or_404(BarriersToParticipation,
                applicant__application_round=current_round,
                applicant__applicant__account__username=self.kwargs['applicant_username'],
                )
        # Only allow people to edit their essays if the flag has been set.
        if not essay.applicant_should_update:
            raise PermissionDenied('You cannot edit your essay at this time.')
        return essay

    def get_success_url(self):
        self.object.applicant_should_update = False
        self.object.save()
        return reverse('eligibility-results')

class NotifySchoolInformationUpdating(LoginRequiredMixin, ComradeRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        current_round = get_current_round_for_initial_application()
        if not request.user.is_staff:
            raise PermissionDenied("Only Outreachy organizers can ask applicants to revise their school information.")

        school_info = get_object_or_404(SchoolInformation,
                applicant__application_round=current_round,
                applicant__applicant__account__username=self.kwargs['applicant_username'],
                )
        school_info.applicant_should_update = True
        school_info.save()
        # Notify applicant their essay needs review
        email.applicant_school_info_needs_updated(school_info.applicant.applicant, request)
        return redirect(reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            }))

class SchoolInformationUpdate(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    model = SchoolInformation

    fields = [
            'current_academic_calendar',
            'next_academic_calendar',
            'school_term_updates',
            ]

    def get_object(self):
        current_round = get_current_round_for_initial_application()
        # Only allow applicants to revise their own essays
        if self.request.user.comrade.account.username != self.kwargs['applicant_username']:
            raise PermissionDenied('You can only edit your own school information.')
        school_info = get_object_or_404(SchoolInformation,
                applicant__application_round=current_round,
                applicant__applicant__account__username=self.kwargs['applicant_username'],
                )
        return school_info

    def get_context_data(self, **kwargs):
        current_round = self.object.applicant.application_round
        school_terms = self.object.applicant.schooltimecommitment_set.all()
        context = super(SchoolInformationUpdate, self).get_context_data(**kwargs)
        context.update({
            'current_round': current_round,
            'school_terms': school_terms,
            })
        return context

    def get_success_url(self):
        self.object.applicant_should_update = False
        self.object.save()
        return reverse('eligibility-results')


def get_or_create_application_reviewer_and_review(self):
    # Only allow approved reviewers to rate applications for the current round
    current_round = get_current_round_for_initial_application()

    try:
        reviewer = ApplicationReviewer.objects.get(
            comrade=self.request.user.comrade,
            reviewing_round=current_round,
            approval_status=ApprovalStatus.APPROVED,
        )
    except ApplicationReviewer.DoesNotExist:
        raise PermissionDenied("You are not currently an approved application reviewer.")

    application = get_object_or_404(ApplicantApproval,
            applicant__account__username=self.kwargs['applicant_username'],
            application_round=current_round)

    # If the reviewer gave an essay review, update it. Otherwise create a new review.
    try:
        review = InitialApplicationReview.objects.get(
                application=application,
                reviewer=reviewer)
    except InitialApplicationReview.DoesNotExist:
        review = InitialApplicationReview(application=application, reviewer=reviewer)

    return (application, reviewer, review)

class SetReviewOwner(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        application, requester, review = get_or_create_application_reviewer_and_review(self)
        # Only allow approved reviewers to change review owners
        if self.kwargs['owner'] == 'None':
            reviewer = None
        else:
            reviewer = get_object_or_404(ApplicationReviewer,
                    comrade__account__username=self.kwargs['owner'],
                    reviewing_round=application.application_round,
                    approval_status=ApprovalStatus.APPROVED)

        application.review_owner = reviewer
        application.save()

        return redirect(reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            }))

class EssayRating(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        application, reviewer, review = get_or_create_application_reviewer_and_review(self)

        rating = kwargs['rating']
        if rating == "STRONG":
            review.essay_rating = review.STRONG
        elif rating == "GOOD":
            review.essay_rating = review.GOOD
        elif rating == "MAYBE":
            review.essay_rating = review.MAYBE
        elif rating == "UNCLEAR":
            review.essay_rating = review.UNCLEAR
        elif rating == "UNRATED":
            review.essay_rating = review.UNRATED
        elif rating == "NOBIAS":
            review.essay_rating = review.NOBIAS
        elif rating == "NOTUNDERSTOOD":
            review.essay_rating = review.NOTUNDERSTOOD
        elif rating == "SPAM":
            review.essay_rating = review.SPAM
        review.save()

        return redirect(reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            }))

# When reviewing the application's time commitments, there are several red flags
# reviewers can set or unset.
class ChangeRedFlag(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        flags = [
                'review_school',
                'missing_school',
                'review_work',
                'missing_work',
                'incorrect_dates',
                ]

        # validate input
        flag_value = kwargs['flag_value']
        flag = kwargs['flag']
        if flag_value != 'True' and flag_value != 'False':
            raise PermissionDenied('Time commitment review flags must be True or False.')
        if flag not in flags:
            raise PermissionDenied('Unknown time commitment review flag.')

        application, reviewer, review = get_or_create_application_reviewer_and_review(self)

        if flag == "review_school":
            if flag_value == 'True':
                review.review_school = True
            elif flag_value == 'False':
                review.review_school = False
        elif flag == "missing_school":
            if flag_value == 'True':
                review.missing_school = True
            elif flag_value == 'False':
                review.missing_school = False
        elif flag == "review_work":
            if flag_value == 'True':
                review.review_work = True
            elif flag_value == 'False':
                review.review_work = False
        elif flag == "missing_work":
            if flag_value == 'True':
                review.missing_work = True
            elif flag_value == 'False':
                review.missing_work = False
        elif flag == "incorrect_dates":
            if flag_value == 'True':
                review.incorrect_dates = True
            elif flag_value == 'False':
                review.incorrect_dates = False
        review.save()

        return redirect(reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            }))

class ReviewCommentUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    model = InitialApplicationReview
    fields = ['comments',]

    def get_object(self):
        application, reviewer, review = get_or_create_application_reviewer_and_review(self)
        return review

    def get_success_url(self):
        return reverse('applicant-review-detail', kwargs={
            'applicant_username': self.kwargs['applicant_username'],
            })

def travel_stipend(request):
    rounds = RoundPage.objects.all().order_by('-internstarts')
    return render(request, 'home/travel_stipend.html', {
        'rounds': rounds,
        })

@login_required
def dashboard(request):
    return render(request, 'home/dashboard.html', {
        'sections': get_dashboard_sections(request),
    })
