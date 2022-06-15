from betterforms.multiform import MultiModelForm
from datetime import datetime, timedelta, timezone, date
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.db import models
from django.forms import inlineformset_factory, ModelForm, modelform_factory, modelformset_factory, ValidationError
from django.forms import widgets
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
from django.views.generic.detail import SingleObjectMixin
from formtools.wizard.views import SessionWizardView
from itertools import chain, groupby
import json
from markdownx.utils import markdownify
from django_registration.forms import RegistrationForm
from django_registration.backends.activation import views as activation_views
import reversion

from . import email

from .dashboard import get_dashboard_sections

from .forms import InviteForm
from .forms import RenameProjectSkillsForm
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
from .models import EmploymentTimeCommitment
from .models import FinalApplication
from .models import get_deadline_date_for
from .models import InformalChatContact
from .models import InternSelection
from .models import InitialApplicationReview
from .models import Feedback1FromMentor
from .models import Feedback1FromIntern
from .models import Feedback2FromMentor
from .models import Feedback2FromIntern
from .models import Feedback3FromMentor
from .models import Feedback3FromIntern
from .models import Feedback4FromMentor
from .models import Feedback4FromIntern
from .models import FinalMentorFeedback
from .models import FinalInternFeedback
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
from .models import skill_is_valid
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

class RegisterUser(activation_views.RegistrationView):
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
        # expects to get that data by calling a get_username method,
        # which only works for actual Django user models. So first we
        # construct a fake user model for it to take apart, containing
        # only the data we want.
        self.activation_data = {'u': user.username}

        # Now, if we have someplace the user is supposed to go after
        # registering, then we save that as well.
        next_url = self.request.POST.get('next')
        if next_url:
            self.activation_data['n'] = next_url

        return super(RegisterUser, self).get_activation_key(self)

    def get_username(self):
        return self.activation_data

    def get_email_field_name(self):
        return "email"

    def get_email_context(self, activation_key):
        return {
            'activation_key': activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'request': self.request,
        }

class PendingRegisterUser(TemplateView):
    template_name = 'django_registration/registration_complete.html'

class ActivationView(activation_views.ActivationView):
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
        return reverse('django_registration_activation_complete') + query

class ActivationCompleteView(TemplateView):
    template_name = 'django_registration/activation_complete.html'

# FIXME - we need a way for comrades to update and re-verify their email address.
class ComradeUpdate(LoginRequiredMixin, UpdateView):
    fields = [
        'public_name',
        'legal_name',
        'pronouns',
        'pronouns_to_participants',
        'pronouns_public',
        'photo',
        'timezone',
        'location',
        'github_url',
        'gitlab_url',
        'nick',
        'blog_url',
        'blog_rss_url',
        'twitter_url',
        'agreed_to_code_of_conduct',
    ]

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

def determine_eligibility(wizard, applicant):
    if not (work_eligibility_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'GENERAL')
    if not (prior_foss_experience_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'GENERAL')

    days_free = applicant.get_time_commitments()["longest_period_free"]
    if days_free is None or days_free < applicant.required_days_free():
        return (ApprovalStatus.REJECTED, 'TIME')

    general_data = wizard.get_cleaned_data_for_step('Work Eligibility')
    if general_data['us_sanctioned_country']:
        return (ApprovalStatus.PENDING, 'SANCTIONED')

    return (ApprovalStatus.PENDING, 'ESSAY')


def get_current_round_for_initial_application():
    """
    People can only submit new initial applications or edit initial
    applications when the application period is open.
    """

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        current_round = RoundPage.objects.get(
            initial_applications_open__lte=today,
            initial_applications_close__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        raise PermissionDenied('The Outreachy application period is closed. If you are an applicant who has submitted an application for an internship project and your time commitments have increased, please contact the Outreachy organizers (see contact link above). Eligibility checking will become available when the next application period opens. Please sign up for the announcements mailing list for an email when the next application period opens: https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce')

    return current_round


def get_current_round_for_initial_application_review():
    """
    Application reviewers need to have finished their work before the
    contribution period begins.
    """

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        current_round = RoundPage.objects.get(
            initial_applications_open__lte=today,
            internstarts__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        raise PermissionDenied('It is too late to review applications.')

    return current_round


def get_current_round_for_sponsors():
    """
    We want to engage sponsors until the interns are announced.
    Otherwise we'll show the generic round schedule.
    """

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    try:
        current_round = RoundPage.objects.get(
            internannounce__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        return None

    return current_round


class EligibilityUpdateView(LoginRequiredMixin, ComradeRequiredMixin, SessionWizardView):
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
            ('Barriers-to-Participation', modelform_factory(BarriersToParticipation,
                fields=(
                    'country_living_in_during_internship',
                    'country_living_in_during_internship_code',
                    'underrepresentation',
                    'employment_bias',
                    'lacking_representation',
                    'systemic_bias',
                    'content_warnings',
                ),
                widgets={
                    'country_living_in_during_internship_code': widgets.HiddenInput,
                },
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
            'Barriers-to-Participation': 'home/eligibility_wizard_essay_questions.html',
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

        # Make sure to commit the object to the database before saving
        # any of the related objects, so they can set their foreign keys
        # to point to this ApplicantApproval object.
        self.object = ApplicantApproval.objects.create(
            applicant=self.request.user.comrade,
            application_round=self.current_round,
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        for form in form_list:
            results = form.save(commit=False)

            # result might be a single value because it's a modelform
            # (WorkEligibility and TimeCommitmentSummary)
            # or a list because it's a modelformsets
            # (VolunteerTimeCommitment, EmploymentTimeCommitment, etc)
            # Make it into a list if it isn't one already.
            if not isinstance(results, list):
                results = [ results ]

            # For each object which contains data from the modelform
            # or modelformsets, we save that database object,
            # after setting the parent pointer.
            for r in results:
                r.applicant = self.object
                r.save()

        # Now that all the related objects are saved, we can determine
        # elegibility from them, which avoids duplicating some code that's
        # already on the models. The cost is reading back some of the objects
        # we just wrote and then re-saving an object, but that isn't a big hit.
        self.object.approval_status, self.object.reason_denied = determine_eligibility(self, self.object)

        # Save the country and country code
        # in a field for Software Freedom Conservancy accounting
        cleaned_data = self.get_cleaned_data_for_step('Barriers-to-Participation')
        if cleaned_data:
            self.object.initial_application_country_living_in_during_internship = cleaned_data['country_living_in_during_internship']
            self.object.initial_application_country_living_in_during_internship_code = cleaned_data['country_living_in_during_internship_code']

        self.object.save()

        return redirect(self.request.GET.get('next', reverse('eligibility-results')))

class EligibilityResults(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/eligibility_results.html'
    context_object_name = 'role'

    def get_object(self):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        # We want to let people know why they can't make contributions, right
        # up until all contributions are closed; but we don't want to confuse
        # people who come back in a future round by showing them old results.
        try:
            current_round = RoundPage.objects.get(
                initial_applications_open__lte=today,
                contributions_close__gt=today,
            )
            current_round.today = today
        except RoundPage.DoesNotExist:
            raise PermissionDenied('The Outreachy application period is closed. Eligibility checking will become available when the next application period opens. Please sign up for the announcements mailing list for an email when the next application period opens: https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce')

        role = Role(self.request.user, current_round)
        if not role.is_applicant:
            raise Http404("No initial application in this round.")
        return role


class ViewInitialApplication(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/applicant_review_detail.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super(ViewInitialApplication, self).get_context_data(**kwargs)
        context['current_round'] = self.object.application_round
        context['role'] = self.role
        return context

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()

        self.role = Role(self.request.user, current_round)

        if not self.role.is_organizer and not self.role.is_reviewer:
            raise PermissionDenied("You are not authorized to review applications.")

        return get_object_or_404(ApplicantApproval,
                    applicant__account__username=self.kwargs['applicant_username'],
                    application_round=current_round)

class ProcessInitialApplication(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/process_initial_application.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super(ProcessInitialApplication, self).get_context_data(**kwargs)
        context['current_round'] = self.object.application_round
        context['role'] = self.role
        return context

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()

        self.role = Role(self.request.user, current_round)

        if not self.role.is_organizer and not self.role.is_reviewer:
            raise PermissionDenied("You are not authorized to review applications.")

        return get_object_or_404(ApplicantApproval,
                    applicant__account__username=self.kwargs['applicant_username'],
                    application_round=current_round)

def promote_page(request):
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    # For the purposes of this view, a round is current until
    # initial application period ends. After that, there's
    # no point in getting people to apply to that round.
    try:
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            initial_applications_close__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        current_round = None

    return render(request, 'home/promote.html',
            {
            'current_round' : current_round,
            },
            )

def past_rounds_page(request):
    return render(request, 'home/past_rounds.html',
            {
                'rounds' : RoundPage.objects.all().order_by('internstarts'),
            },
            )

def current_round_page(request):
    closed_approved_projects = []
    ontime_approved_projects = []
    example_skill = ProjectSkill

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    # For the purposes of this view, a round is current until its
    # intern selections are announced, and then it becomes one of
    # the "previous" rounds.

    try:
        previous_round = RoundPage.objects.filter(
            internannounce__lte=today,
        ).latest('internstarts')
        previous_round.today = today
    except RoundPage.DoesNotExist:
        previous_round = None

    try:
        # Keep RoundPage.serve() in sync with this.
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            internannounce__gt=today,
        )
        current_round.today = today
    except RoundPage.DoesNotExist:
        current_round = None

    role = Role(request.user, current_round)
    if current_round is not None:
        all_participations = current_round.participation_set.approved().order_by('community__name')
        apps_open = current_round.initial_applications_open.has_passed()

        if apps_open or role.is_volunteer:
            # Anyone should be able to see all projects if the initial
            # application period is open. This builds up excitement in
            # applicants and gets them to complete an initial application. Note
            # in the template, links are still hidden if the initial
            # application is pending or rejected.
            approved_participations = all_participations

        elif request.user.is_authenticated:
            # Approved coordinators should be able to see their communities
            # even if the community isn't approved yet.
            approved_participations = all_participations.filter(
                community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                community__coordinatorapproval__coordinator__account=request.user,
            )

        else:
            # Otherwise, no communities should be visible.
            approved_participations = all_participations.none()

        for p in approved_participations:
            projects = p.project_set.approved().filter(new_contributors_welcome=False)
            if projects:
                closed_approved_projects.append((p, projects))
            projects = p.project_set.approved().filter(new_contributors_welcome=True)
            if projects:
                ontime_approved_projects.append((p, projects))
            # List communities that are approved but don't have any projects yet
            if not p.project_set.approved():
                ontime_approved_projects.append((p, None))

    return render(request, 'home/round_page_with_communities.html',
            {
            'current_round' : current_round,
            'previous_round' : previous_round,
            'closed_projects': closed_approved_projects,
            'ontime_projects': ontime_approved_projects,
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
        previous_round.today = today
    except RoundPage.DoesNotExist:
        previous_round = None

    try:
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            internstarts__gt=today,
        )
        current_round.today = today
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
                if participation_info.is_pending():
                    pending_communities.append(c)
                elif participation_info.is_approved():
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


def community_read_only_view(request, community_slug):
    """
    This is the page for volunteers, mentors, and coordinators. It's a
    read-only page that displays information about the community, what projects
    are accepted, and how volunteers can help. If the community isn't
    participating in this round, the page displays instructions for being
    notified or signing the community up to participate.
    """

    community = get_object_or_404(Community, slug=community_slug)

    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)

    participation_info = None

    # For the purposes of this view, a round is current until its interns start
    # their internships, and then it becomes one of the "previous" rounds.

    try:
        current_round = RoundPage.objects.get(
            pingnew__lte=today,
            internstarts__gt=today,
        )
        current_round.today = today
        previous_round = None
    except RoundPage.DoesNotExist:
        current_round = None
        try:
            previous_round = community.rounds.filter(
                internstarts__lte=today,
                participation__approval_status=ApprovalStatus.APPROVED,
            ).latest('internstarts')
            previous_round.today = today
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
    ontime_projects = [p for p in projects if p.new_contributors_welcome]
    closed_projects = [p for p in projects if not p.new_contributors_welcome]
    example_skill = ProjectSkill
    current_round = participation_info.participating_round

    role = Role(request.user, current_round)

    approved_coordinator_list = CoordinatorApproval.objects.none()
    if request.user.is_authenticated:
        approved_coordinator_list = participation_info.community.coordinatorapproval_set.approved()

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

    approved_to_see_all_project_details = approved_coordinator or role.is_approved_applicant or role.is_volunteer

    return render(request, 'home/community_landing.html',
            {
            'participation_info': participation_info,
            'ontime_projects': ontime_projects,
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
            'reason_for_participation',
            'mentorship_programs',
            'repositories',
            'licenses_used',
            'approved_license',
            'no_proprietary_software',
            'cla',
            'dco',
            'unapproved_license_description',
            'proprietary_software_description',
            'participating_orgs',
            'approved_advertising',
            'unapproved_advertising_description',
            'governance',
            'participating_orgs_in_goverance',
            'code_of_conduct',
            'coc_committee',
            'demographics',
            'inclusive_practices',
            ]

    def get_form(self):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        try:
            self.current_round = RoundPage.objects.filter(
                lateorgs__gt=today,
            ).earliest('lateorgs')
            self.current_round.today = today
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

        # Send email
        email.notify_organizers_of_new_community(self.object)

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
    fields = [
            'name',
            'website',
            'description',
            'long_description',
            'tutorial']

    def get_object(self):
        community = super(CommunityUpdate, self).get_object()
        if not community.is_coordinator(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

    def get_success_url(self):
        return self.object.get_preview_url()

class GeneralFundingApplication(LoginRequiredMixin, UpdateView):
    model = Community
    slug_url_kwarg = 'community_slug'
    form_class = modelform_factory(
            Community,
            fields=(
                'inclusive_participation',
                'additional_sponsors',
                'humanitarian_community',
                'general_funding_application',
                'open_science_community',
                'open_science_practices',
                'open_science_funder_questions',
                ),
            field_classes={
                'humanitarian_community': RadioBooleanField,
                'open_science_community': RadioBooleanField,
                }
    )
    template_name = 'home/general_funding_application.html'

    def get_object(self):
        community = super(GeneralFundingApplication, self).get_object()
        if not community.is_coordinator(self.request.user):
            raise PermissionDenied("You are not an approved coordinator for this community.")
        return community

    def get_success_url(self):
        if self.kwargs['new'] == 'True':
            return reverse('community-update', kwargs = {
                'community_slug': self.object.slug,
                })
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

        # Workflow changes depending on whether we create a new Participation
        # or just update an existing one.
        self.new = False

        # FIXME: probably should raise PermissionDenied, not Http404, outside of deadlines

        # For most purposes, this form is available right up to intern announcement...
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)
        participating_round = get_object_or_404(
            RoundPage,
            slug=self.kwargs['round_slug'],
            pingnew__lte=today,
            internannounce__gt=today,
        )

        # ...except submitting new communities cuts off at the lateorgs deadline.
        if participating_round.lateorgs.has_passed():
            return get_object_or_404(
                Participation,
                community=community,
                participating_round=participating_round,
            )

        try:
            return Participation.objects.get(
                    community=community,
                    participating_round=participating_round)
        except Participation.DoesNotExist:
            self.new = True
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

    def get_success_url(self):
        return reverse('community-general-funding', kwargs = {
            'community_slug': self.object.community.slug,
            'new': self.new,
            })

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
            'current_round': project.round(),
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


class InviteMentor(LoginRequiredMixin, ComradeRequiredMixin, FormView, SingleObjectMixin):
    template_name = 'home/invite-mentor.html'
    form_class = InviteForm

    def get_form(self, *args, **kwargs):
        # This method is called during both GET and POST, before
        # get_context_data or form_valid, but after the login checks have run.
        # So it's a semi-convenient common place to set self.object.
        self.object = project = get_object_or_404(
            Project,
            project_round__community__slug=self.kwargs['community_slug'],
            project_round__participating_round__slug=self.kwargs['round_slug'],
            slug=self.kwargs['project_slug'],
        )

        user = self.request.user
        if not project.is_mentor(user) and not project.project_round.community.is_coordinator(user):
            raise PermissionDenied("Only approved project mentors or community coordinators can invite additional mentors.")

        return super(InviteMentor, self).get_form(*args, **kwargs)

    def form_valid(self, form):
        email.invite_mentor(self.object, form.get_address(), self.request)
        return redirect('dashboard')


class MentorApprovalAction(ApprovalStatusAction):
    fields = [
            'understands_applicant_time_commitment',
            'understands_intern_time_commitment',
            'instructions_read',
            'understands_mentor_contract',
            'employer',
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

    def get_context_data(self, **kwargs):
        employers = set(MentorApproval.objects.exclude(employer='Prefer not to say').exclude(employer='Unemployed').exclude(employer='Self employed').values_list('employer', flat=True).distinct())
        employers.update([
                    "Akamai",
                    "Amazon Web Services (AWS)",
                    "Automattic",
                    "Berkeley Institute For Data Science (BIDS)",
                    "Bloomberg",
                    "Ceph Foundation",
                    "CISCO",
                    "Cloud Native Computing Foundation (CNCF)",
                    "Cloudera",
                    "Code for Science & Society (CSS)",
                    "Codethink",
                    "Codeweavers",
                    "Collabora",
                    "Comcast",
                    "Continuous Delivery Foundation (CDF)",
                    "Creative Commons Corporation",
                    "DigitalOcean",
                    "Discourse",
                    "Electronic Frontier Foundation (EFF)",
                    "Endless",
                    "F# Software Foundation",
                    "Fondation partenariale Inria / Fondation OCaml",
                    "Ford Foundation",
                    "Free Software Foundation (FSF)",
                    "GatsbyJS",
                    "GitHub",
                    "GitLab",
                    "GNOME Foundation Inc",
                    "Goldman Sachs",
                    "Google",
                    "Haiku, Inc.",
                    "Hewlett Packard Enterprise",
                    "IBM",
                    "Igalia",
                    "Indeed",
                    "Intel Corporation",
                    "Lightbend",
                    "Linaro",
                    "Linux Foundation",
                    "Mapbox",
                    "Mapzen",
                    "Measurement Lab",
                    "Microsoft",
                    "Mozilla Corporation",
                    "Mozilla Foundation",
                    "NumFOCUS, Inc",
                    "Open Bioinformatics Foundation (OBF)",
                    "OpenHatch",
                    "OpenStack Foundation",
                    "Open Technology Institute",
                    "Python Software Foundation",
                    "Rackspace",
                    "Red Hat",
                    "Samsung",
                    "Shopify",
                    "Software in the Public Interest (SPI)",
                    "Terasology Foundation",
                    "The Open Information Security Foundation (OISF)",
                    "The Perl Foundation (TPF)",
                    "Tidelift",
                    "Twitter",
                    "United Nations Foundation",
                    "University of Cambridge",
                    "Wellcome Trust",
                    "Wikimedia Foundation",
                    "Xen Project",
                    "Zulip",
                    "Yocto Project",
                    "X.org Foundation",

                ])
        employers = ([
                    "Prefer not to say",
                    "Unemployed",
                    "Self employed",
            ]) + sorted(employers)

        context = super(MentorApprovalAction, self).get_context_data(**kwargs)
        context.update({
            # Make sure that someone can't inject code in another person's
            # browser by adding a maliciously encoded employer.
            # json.dumps() takes the employer list (encoded as a Python list)
            # and encodes the list in JavaScript object notation.
            # mark_safe means this data has already been cleaned,
            # and the Django template code shouldn't clean it.
            'employers': mark_safe(json.dumps(employers)),
            })
        return context

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
            return self.object.project.reverse('project-skills-edit')

        return self.object.project.get_preview_url()

    def notify(self):
        if self.prior_status != self.target_status:
            email.approval_status_changed(self.object, self.request)
            if self.target_status == MentorApproval.APPROVED:
                interns = self.object.project.internselection_set.exclude(funding_source=InternSelection.NOT_FUNDED)

                # If we're adding a co-mentor after Outreachy organizers have
                # approved intern selections, then only tell the new co-mentor
                # about the approved interns.
                current_round = self.object.project.round()
                if current_round.internapproval.has_passed():
                    interns = interns.filter(organizer_approved=True)

                for intern_selection in interns:
                    email.co_mentor_intern_selection_notification(
                        intern_selection,
                        [self.object.mentor.email_address()],
                        self.request,
                    )

class ProjectAction(ApprovalStatusAction):
    fields = ['approved_license', 'no_proprietary_software', 'longevity', 'community_size', 'short_title', 'long_description', 'minimum_system_requirements', 'contribution_tasks', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'intern_tasks', 'intern_benefits', 'community_benefits', 'unapproved_license_description', 'proprietary_software_description', 'new_contributors_welcome']

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
            return self.object.reverse('project-skills-edit')
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
        if not project.is_approved() and deadline.has_passed():
            raise PermissionDenied("The project submission and approval deadline ({date}) has passed. Please sign up for the announcement mailing list for a call for mentors for the next Outreachy internship round. https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce".format(date=deadline))
        return project

    def get_success_url(self):
        return reverse(self.next_view, kwargs=self.kwargs)

class ProjectSkillsEditPage(BaseProjectEditPage):
    template_name_suffix = '_skills_form'
    form_class = inlineformset_factory(Project, ProjectSkill, fields='__all__')
    next_view = 'communication-channels-edit'

    def get_context_data(self, **kwargs):
        context = super(ProjectSkillsEditPage, self).get_context_data(**kwargs)
        suggestions = list(set([ps.skill for ps in ProjectSkill.objects.all()]))
        clean_suggestions = []
        for s in suggestions:
            try:
                skill_is_valid(s)
                clean_suggestions.append(s)
            except ValidationError:
                pass
        context.update({
            # Make sure that someone can't inject code in another person's
            # browser by adding a maliciously encoded project skill.
            # json.dumps() takes the skills list (encoded as a Python list)
            # and encodes the list in JavaScript object notation.
            # mark_safe means this data has already been cleaned,
            # and the Django template code shouldn't clean it.
            'suggested_skills': mark_safe(json.dumps(clean_suggestions)),
            })
        return context

class CommunicationChannelsEditPage(BaseProjectEditPage):
    template_name_suffix = '_channels_form'
    form_class = inlineformset_factory(Project, CommunicationChannel, fields='__all__')
    next_view = 'project-read-only'

class ProjectSkillsRename(LoginRequiredMixin, FormView):
    template_name = 'home/rename_project_skills.html'
    form_class = RenameProjectSkillsForm

    def get_form(self, *args, **kwargs):
        # This method is called during both GET and POST, before
        # get_context_data or form_valid, but after the login checks have run.
        # So it's a semi-convenient common place to set self.object.
        user = self.request.user
        if not user.is_staff:
            raise PermissionDenied("Only Outreachy organizers can rename project skills across all submitted projects.")

        ids = self.request.GET.get('ids').split(',')
        self.project_skills = ProjectSkill.objects.filter(pk__in=ids).order_by('skill')

        return super(ProjectSkillsRename, self).get_form(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectSkillsRename, self).get_context_data(**kwargs)
        context.update({
            'project_skills' : self.project_skills,
            })
        return context

    def form_valid(self, form):
        new_name = form.cleaned_data['new_name']
        # iterate over self.project_skills, set new name
        for ps in self.project_skills:
            ps.skill = new_name
            ps.save()
        # Redirect back to the admin page for listing all ProjectSkill objects
        return redirect('admin:home_projectskill_changelist')

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

        current_round = project.round()
        role = Role(self.request.user, current_round)

        contributions = role.application.contribution_set.filter(
                project=project)
        try:
            final_application = role.application.finalapplication_set.get(
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

        current_round = project.round()
        role = Role(self.request.user, current_round)

        try:
            application = role.application.finalapplication_set.get(
                    project=project)
        except FinalApplication.DoesNotExist:
            application = None

        if not current_round.contributions_open.has_passed():
            raise PermissionDenied("You cannot record a contribution until the Outreachy application period opens.")

        if current_round.contributions_close.has_passed() and application == None:
            raise PermissionDenied("Editing or recording new contributions is closed at this time to applicants who have not created a final application.")

        if current_round.internannounce.has_passed():
            raise PermissionDenied("Editing or recording new contributions is closed at this time.")

        if 'contribution_id' not in self.kwargs:
            return Contribution(applicant=role.application, project=project)
        return get_object_or_404(
            Contribution,
            applicant=role.application,
            project=project,
            pk=self.kwargs['contribution_id'],
        )

    def get_success_url(self):
        return self.object.project.get_contributions_url()

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

        current_round = project.round()

        if not current_round.contributions_open.has_passed():
            raise PermissionDenied("You cannot rate an applicant until the Outreachy application period opens.")

        if current_round.has_last_day_to_add_intern_passed():
            raise PermissionDenied("Outreachy interns cannot be rated at this time.")

        applicant = get_object_or_404(
            current_round.applicantapproval_set.approved(),
            applicant__account__username=kwargs['username'],
        )

        application = get_object_or_404(FinalApplication, applicant=applicant, project=project)
        rating = kwargs['rating']
        if rating in [c[0] for c in application.RATING_CHOICES]:
            application.rating = kwargs['rating']
            application.save()

        return redirect(project.get_applicants_url() + "#rating")

class FinalApplicationAction(ApprovalStatusAction):
    fields = [
            'time_correct',
            'time_updates',
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
            account = get_object_or_404(User, username=username)
        else:
            account = self.request.user

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round__slug=self.kwargs['round_slug'],
                project_round__approval_status=ApprovalStatus.APPROVED)

        current_round = project.round()
        role = Role(account, current_round, self.request.user)

        if not current_round.contributions_open.has_passed():
            raise PermissionDenied("You can't submit a final application until the Outreachy application period opens.")

        if current_round.contributions_close.has_passed():
            raise PermissionDenied("This project is closed to final applications.")

        # Only allow eligible applicants to apply
        if not role.is_approved_applicant:
            raise PermissionDenied("You are not an eligible applicant or you have not filled out the eligibility check.")

        try:
            return FinalApplication.objects.get(applicant=role.application, project=project)
        except FinalApplication.DoesNotExist:
            return FinalApplication(applicant=role.application, project=project)

    def get_success_url(self):
        return self.object.project.get_contributions_url()

class ProjectApplicants(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/project_applicants.html'

    def get_context_data(self, **kwargs):
        # Make sure both the Community, Project, and mentor are approved
        # Note that accessing URL parameters like project_slug off kwargs only
        # works because this is a TemplateView. For the various kinds of
        # DetailViews, you have to use self.kwargs instead.
        project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug'],
            approval_status=ApprovalStatus.APPROVED,
            project_round__community__slug=self.kwargs['community_slug'],
            project_round__participating_round__slug=self.kwargs['round_slug'],
            project_round__approval_status=ApprovalStatus.APPROVED,
        )

        current_round = project.round()

        # Note that there's no reason to ever keep someone who was a
        # coordinator or mentor in a past round from looking at who applied in
        # that round.

        if not self.request.user.is_staff and not project.project_round.community.is_coordinator(self.request.user) and not project.round().is_mentor(self.request.user):
            raise PermissionDenied("You are not an approved mentor for this project.")

        contributions = project.contribution_set.filter(
                applicant__approval_status=ApprovalStatus.APPROVED).order_by(
                "applicant__applicant__public_name", "date_started")
        internship_total_days = current_round.internends - current_round.internstarts
        try:
            mentor_approval = project.mentorapproval_set.approved().get(
                mentor__account=self.request.user,
            )
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
            'is_staff': self.request.user.is_staff,
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

    current_round.today = today

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

class ActiveTrustedVolunteersListView(UserPassesTestMixin, ListView):
    template_name = 'home/trusted_volunteers.html'

    def get_queryset(self):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        # For all interns with active internships, who are approved by Outreachy organizers,
        interns = InternSelection.objects.filter(
                organizer_approved=True,
                intern_starts__lte=today,
                intern_ends__gte=today)

        # Find all mentors who signed up to mentor this intern,
        # and all approved coordinators for the intern's community.
        #
        # This means mentors who didn't select an intern,
        # or coordiantors from communities who didn't select any interns don't
        # get re-subscribed to the mentors' mailing list or invited to the chat.
        return Comrade.objects.filter(
                models.Q(
                    mentorapproval__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__mentorrelationship__intern_selection__in=interns,
                ) | models.Q(
                    coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    coordinatorapproval__community__in=[i.project.project_round.community for i in interns],
                )
            ).order_by('public_name').distinct()

    def test_func(self):
        return self.request.user.is_staff

class ActiveInternshipContactsView(UserPassesTestMixin, TemplateView):
    template_name = 'home/active_internship_contacts.html'

    def get_context_data(self, **kwargs):
        now = datetime.now(timezone.utc)
        today = get_deadline_date_for(now)

        # For all interns with active internships, who are approved by Outreachy organizers,
        # or past interns in good standing where Outreachy organizers have not processed their final internship stipend.
        interns = InternSelection.objects.filter(
                models.Q(
                    organizer_approved=True,
                    project__project_round__participating_round__internannounce__lte=today,
                    intern_ends__gte=today,
                ) | models.Q(
                    organizer_approved=True,
                    project__project_round__participating_round__internannounce__lte=today,
                    in_good_standing=True,
                    finalmentorfeedback__organizer_payment_approved=None,
                )).order_by('project__project_round__community__name').order_by('-project__project_round__participating_round__internstarts')

        mentors_and_coordinators = Comrade.objects.filter(
                models.Q(
                    mentorapproval__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__mentorrelationship__intern_selection__in=interns,
                ) | models.Q(
                    coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    coordinatorapproval__community__in=[i.project.project_round.community for i in interns],
                )
            ).order_by('public_name').distinct()

        context = super(ActiveInternshipContactsView, self).get_context_data(**kwargs)
        context.update({
            'interns': interns,
            'mentors_and_coordinators': mentors_and_coordinators,
            })
        return context

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
        if not internship.round().internannounce.has_passed():
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
    self.applicant = get_object_or_404(
        current_round.applicantapproval_set.approved(),
        applicant__account__username=self.kwargs['applicant_username'],
    )

# Passed round_slug, community_slug, project_slug, applicant_username
class InternSelectionUpdate(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, FormView):
    form_class = InternSelectionForm
    template_name = 'home/internselection_form.html'

    def get_form_kwargs(self):
        kwargs = super(InternSelectionUpdate, self).get_form_kwargs()

        current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

        if not current_round.contributions_open.has_passed():
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
            self.mentor_approval = self.project.mentorapproval_set.approved().get(
                mentor__account=self.request.user,
            )
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
        context['current_round'] = self.project.round()
        return context

    def form_valid(self, form):
        form['rating'].save()

        # We can't use get or create here, in case the payment dates have changed
        # between when the intern was initially selected and when a co-mentor signed up
        was_intern_selection_created = False
        try:
            intern_selection = InternSelection.objects.get(
                applicant=self.applicant,
                project=self.project,
                )
        except InternSelection.DoesNotExist:
            was_intern_selection_created = True

            current_round = self.project.round()
            intern_selection = InternSelection.objects.create(
                    applicant=self.applicant,
                    project=self.project,
                    intern_starts=current_round.internstarts,
                    initial_feedback_opens=current_round.initialfeedback - timedelta(days=7),
                    initial_feedback_due=current_round.initialfeedback,
                    midpoint_feedback_opens=current_round.midfeedback - timedelta(days=7),
                    midpoint_feedback_due=current_round.midfeedback,
                    intern_ends=current_round.internends,
                    final_feedback_opens=current_round.finalfeedback - timedelta(days=7),
                    final_feedback_due=current_round.finalfeedback,
                    )
            if current_round.feedback3_due:
                    intern_selection.feedback3_opens = current_round.feedback3_due - timedelta(days=7)
                    intern_selection.feedback3_due = current_round.feedback3_due

        # Fill in the date and IP address of the signed contract
        signed_contract = form['contract'].save(commit=False)
        signed_contract.date_signed = datetime.now(timezone.utc)
        signed_contract.ip_address = self.request.META.get('REMOTE_ADDR')
        signed_contract.text = self.mentor_agreement
        signed_contract.save()
        mentor_relationship = MentorRelationship(
                intern_selection=intern_selection,
                mentor=self.mentor_approval,
                contract=signed_contract).save()

        # If we just created this intern selection, email all co-mentors and
        # encourage them to sign the mentor agreement.
        if was_intern_selection_created:
            email.co_mentor_intern_selection_notification(
                intern_selection,
                [
                    mentor_approval.mentor.email_address()
                    for mentor_approval in self.project.mentorapproval_set.approved()
                    # skip the current visitor, who just signed
                    if mentor_approval != self.mentor_approval
                ],
                self.request,
            )

        # Send emails about any project conflicts
        email.intern_selection_conflict_notification(intern_selection, self.request)
        return redirect(self.project.get_applicants_url() + "#rating")

# Passed round_slug, community_slug, project_slug, applicant_username
class InternRemoval(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, DeleteView):
    model = InternSelection
    template_name = 'home/intern_removal_form.html'

    def get_object(self):
        current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])

        # If the internship has been announced
        # then only Outreachy organizers should remove interns
        # by setting them not in good standing on the alums page.
        if current_round.internannounce.has_passed():
            raise PermissionDenied("Only Outreachy organizers can remove an intern after the internship starts.")

        set_project_and_applicant(self, current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)
        self.mentor_relationships = self.intern_selection.mentorrelationship_set.all()

        # Only allow approved mentors to remove interns
        # Coordinators can set the funding to 'Not funded'
        # Organizers can set the InternSelection.organizer_approved to False
        try:
            self.mentor_approval = self.project.mentorapproval_set.approved().get(
                mentor__account=self.request.user,
            )
        except MentorApproval.DoesNotExist:
            raise PermissionDenied("Only approved mentors can select an applicant as an intern")
        return self.intern_selection

    def get_context_data(self, **kwargs):
        context = super(InternRemoval, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['community'] = self.project.project_round.community
        context['applicant'] = self.applicant
        context['current_round'] = self.project.round()
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

        return self.project.get_applicants_url() + "#rating"

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
        'current_round': intern_selection.project.round(),
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
            self.mentor_approval = self.project.mentorapproval_set.approved().get(
                mentor__account=self.request.user,
            )
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
        return self.project.get_applicants_url() + "#rating"

class InternFund(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = get_object_or_404(RoundPage, slug=kwargs['round_slug'])

        if not current_round.contributions_open.has_passed():
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

        return redirect(self.project.project_round.reverse('community-applicants') + "#interns")

class InternApprove(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = get_object_or_404(RoundPage, slug=kwargs['round_slug'])

        if not current_round.contributions_open.has_passed():
            raise PermissionDenied("You cannot approve an Outreachy intern until the application period opens.")

        if current_round.has_last_day_to_add_intern_passed():
            raise PermissionDenied("Approval status for Outreachy interns cannot be changed at this time.")

        set_project_and_applicant(self, current_round)
        self.intern_selection = get_object_or_404(InternSelection,
                applicant=self.applicant,
                project=self.project)

        if self.intern_selection.funding_source not in (InternSelection.GENERAL_FUNDED, InternSelection.ORG_FUNDED):
            raise PermissionDenied("Outreachy interns cannot be approvde until they have a funding source selected.")

        # Only allow approved organizers to approve interns
        if not request.user.is_staff:
            raise PermissionDenied("Only organizers can approve interns.")

        approval = kwargs['approval']
        if approval == "Approved":
            self.intern_selection.organizer_approved = True
        elif approval == "Rejected":
            self.intern_selection.organizer_approved = False
        elif approval == "Undecided":
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

        return redirect('alums')

# Passed round_slug, community_slug, project_slug, (get applicant from request.user)
class InternAgreementSign(LoginRequiredMixin, ComradeRequiredMixin, CreateView):
    model = SignedContract
    template_name = 'home/internrelationship_form.html'
    fields = ('legal_name',)

    def set_project_and_intern_selection(self):
        self.current_round = get_object_or_404(RoundPage, slug=self.kwargs['round_slug'])
        if not self.current_round.internannounce.has_passed():
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
    current_round = get_object_or_404(RoundPage, slug=round_slug)
    return render(request, 'home/blog/round-statistics.html', {
        'current_round': current_round,
        })

def blog_schedule_changes(request):
    try:
        changed_round = RoundPage.objects.get(
            contributions_open__gte='2019-07-23',
            contributions_open__lte='2019-12-01',
        )
    except RoundPage.DoesNotExist:
        changed_round = None
    return render(request, 'home/blog/2019-07-23-outreachy-schedule-changes.html', {
        'changed_round': changed_round,
        })

def blog_2019_pick_projects(request):
    try:
        changed_round = RoundPage.objects.get(
            contributions_open__gte='2019-07-23',
            contributions_open__lte='2019-12-01',
        )
    except RoundPage.DoesNotExist:
        changed_round = None
    return render(request, 'home/blog/2019-10-01-picking-a-project.html', {
        'changed_round': changed_round,
        })

def blog_2019_10_18_open_projects(request):
    return render(request, 'home/blog/2019-10-18-open-projects.html')

def blog_2020_03_covid(request):
    return render(request, 'home/blog/2020-03-27-outreachy-response-to-covid-19.html')

def blog_2020_08_23_initial_applications_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2020-11-01',
            internends__lte='2021-04-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2020-08-23-initial-applications-open.html', {
        'current_round': current_round,
        })

def blog_2021_01_15_community_cfp_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2021-05-01',
            internends__lte='2021-09-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2021-01-15-community-cfp-open.html', {
        'current_round': current_round,
        })

def blog_2021_02_01_initial_applications_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2021-05-01',
            internends__lte='2021-09-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2021-02-01-initial-applications-open.html', {
        'current_round': current_round,
        })

def blog_2021_03_23_fsf_participation_barred(request):
    return render(request, 'home/blog/2021-03-23-fsf-participation-barred.html')

def blog_2021_03_30_contribution_period_open(request):
    return render(request, 'home/blog/2021-03-30-contribution-period-open.html')

def blog_2021_08_13_initial_applications_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2021-08-01',
            internends__lte='2022-04-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2021-08-13-initial-applications-open.html', {
        'current_round': current_round,
        })

def blog_2021_08_18_cfp_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2021-08-01',
            internends__lte='2022-04-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2021-08-18-cfp-open.html', {
        'current_round': current_round,
        })

def blog_2021_10_outreachy_hiring(request):
    return render(request, 'home/blog/2021-10-12-outreachy-is-hiring.html')

def blog_2022_01_10_cfp_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2022-05-01',
            internends__lte='2022-09-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2022-01-10-community-cfp-open.html', {
        'current_round': current_round,
        })

def blog_2022_02_04_initial_applications_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2022-05-01',
            internends__lte='2022-09-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2022-02-04-initial-applications-open.html', {
        'current_round': current_round,
        })

def blog_2022_04_15_new_community_manager(request):
    return render(request, 'home/blog/2022-04-15-new-outreachy-community-manager.html')

def blog_2022_06_14_remembering_marina(request):
    return render(request, 'home/blog/2022-06-14-remembering-and-honoring-marina.html')

class InitialMentorFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback1FromMentor,
            fields=(
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',
                'last_contact',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',
                'talk_about_project_progress',
                'blog_created',
                'mentors_report',
                'progress_report',
                'full_time_effort',
                'actions_requested',
            ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'blog_created': RadioBooleanField,
                'in_contact': RadioBooleanField,
                'provided_onboarding': RadioBooleanField,
                'full_time_effort': RadioBooleanField,
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
            feedback = Feedback1FromMentor.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback1FromMentor.DoesNotExist:
            return Feedback1FromMentor(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class InitialInternFeedbackUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback1FromIntern,
            fields=(
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',
                'talk_about_project_progress',
                'blog_created',
                'last_contact',
                'mentor_support',
                'share_mentor_feedback_with_community_coordinator',
                'hours_worked',
                'time_comments',
                'progress_report',
                ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'blog_created': RadioBooleanField,
                'share_mentor_feedback_with_community_coordinator': RadioBooleanField,
                },
            )
    def get_object(self):
        self.internship = intern_in_good_standing(self.request.user)
        if not self.internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = Feedback1FromIntern.objects.get(intern_selection=self.internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback1FromIntern.DoesNotExist:
            return Feedback1FromIntern(intern_selection=self.internship)

    def get_context_data(self, **kwargs):
        context = super(InitialInternFeedbackUpdate, self).get_context_data(**kwargs)
        context['internship'] = self.internship
        return context

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
            }

@login_required
@staff_member_required
def initial_mentor_feedback_export_view(request, round_slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    interns = this_round.get_approved_intern_selections()
    dictionary_list = []
    for i in interns:
        try:
            dictionary_list.append(export_feedback(i.feedback1frommentor))
        except Feedback1FromMentor.DoesNotExist:
            continue
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-initial-feedback.json"'
    return response

@login_required
@staff_member_required
def initial_feedback_summary(request, round_slug):
    current_round = get_object_or_404(RoundPage, slug=round_slug)

    return render(request, 'home/initial_feedback.html',
            {
            'current_round' : current_round,
            },
            )

class Feedback2FromMentorUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback2FromMentor,
            fields=(
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',
                'talk_about_project_progress',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',

                'mentors_report',
                'last_contact',
                'progress_report',

                'full_time_effort',

                'actions_requested',
            ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,

                'full_time_effort': RadioBooleanField,
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
            feedback = Feedback2FromMentor.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback2FromMentor.DoesNotExist:
            return Feedback2FromMentor(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class Feedback2FromInternUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback2FromIntern,
            fields=(
                'share_mentor_feedback_with_community_coordinator',

                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',
                'talk_about_project_progress',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',

                'mentor_support',
                'last_contact',
                'hours_worked',
                'time_comments',
                'progress_report',
                ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,
                'share_mentor_feedback_with_community_coordinator': RadioBooleanField,
            },
            )

    def get_object(self):
        self.internship = intern_in_good_standing(self.request.user)
        if not self.internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = Feedback2FromIntern.objects.get(intern_selection=self.internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback2FromIntern.DoesNotExist:
            return Feedback2FromIntern(intern_selection=self.internship)

    def get_context_data(self, **kwargs):
        context = super(Feedback2FromInternUpdate, self).get_context_data(**kwargs)
        context['internship'] = self.internship
        return context

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

@login_required
@staff_member_required
def midpoint_feedback_summary(request, round_slug):
    current_round = get_object_or_404(RoundPage, slug=round_slug)

    return render(request, 'home/midpoint_feedback.html',
            {
            'current_round' : current_round,
            },
            )

class Feedback3FromMentorUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback3FromMentor,
            fields=(
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',

                'talk_about_project_progress',
                'reviewed_original_timeline',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',

                'mentors_report',
                'last_contact',
                'progress_report',

                'full_time_effort',

                'actions_requested',
            ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'reviewed_original_timeline': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,

                'full_time_effort': RadioBooleanField,
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
            feedback = Feedback3FromMentor.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback3FromMentor.DoesNotExist:
            return Feedback3FromMentor(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class Feedback3FromInternUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback3FromIntern,
            fields=(
                'share_mentor_feedback_with_community_coordinator',

                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',

                'talk_about_project_progress',
                'reviewed_original_timeline',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',

                'mentor_support',
                'last_contact',
                'hours_worked',
                'time_comments',
                'progress_report',
                ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'reviewed_original_timeline': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,
                'share_mentor_feedback_with_community_coordinator': RadioBooleanField,
            },
            )

    def get_object(self):
        self.internship = intern_in_good_standing(self.request.user)
        if not self.internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = Feedback3FromIntern.objects.get(intern_selection=self.internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback3FromIntern.DoesNotExist:
            return Feedback3FromIntern(intern_selection=self.internship)

    def get_context_data(self, **kwargs):
        context = super(Feedback3FromInternUpdate, self).get_context_data(**kwargs)
        context['internship'] = self.internship
        return context

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

@login_required
@staff_member_required
def feedback_3_export_view(request, round_slug):
    this_round = get_object_or_404(RoundPage, slug=round_slug)
    interns = this_round.get_approved_intern_selections()
    dictionary_list = []
    for i in interns:
        try:
            dictionary_list.append(export_feedback(i.feedback3frommentor))
        except Feedback3FromMentor.DoesNotExist:
            continue
    response = JsonResponse(dictionary_list, safe=False)
    response['Content-Disposition'] = 'attachment; filename="' + round_slug + '-midpoint-feedback.json"'
    return response

@login_required
@staff_member_required
def feedback_3_summary(request, round_slug):
    current_round = get_object_or_404(RoundPage, slug=round_slug)

    return render(request, 'home/feedback3.html',
            {
            'current_round' : current_round,
            },
            )

class Feedback4FromMentorUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback4FromMentor,
            fields=(
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',

                'talk_about_project_progress',
                'reviewed_original_timeline',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',
                'mentor_introduced_to_informal_chat_contacts',
                'intern_had_informal_chats',

                'mentors_report',
                'last_contact',
                'progress_report',

                'full_time_effort',

                'actions_requested',

                'recommend_mentoring',
                'mentoring_positive_impacts',
                'mentoring_improvement_suggestions',
                'new_mentor_suggestions',
                'community_positive_impacts',
                'community_improvement_suggestions',
                'additional_feedback',
            ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'reviewed_original_timeline': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,
                'mentor_introduced_to_informal_chat_contacts': RadioBooleanField,
                'intern_had_informal_chats': RadioBooleanField,

                'full_time_effort': RadioBooleanField,
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
            feedback = Feedback4FromMentor.objects.get(intern_selection=internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback4FromMentor.DoesNotExist:
            return Feedback4FromMentor(intern_selection=internship)

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

class Feedback4FromInternUpdate(LoginRequiredMixin, reversion.views.RevisionMixin, UpdateView):
    form_class = modelform_factory(Feedback4FromIntern,
            fields=(
                'share_mentor_feedback_with_community_coordinator',
                'mentor_answers_questions',
                'intern_asks_questions',
                'mentor_support_when_stuck',

                'daily_stand_ups',
                'meets_privately',
                'meets_over_phone_or_video_chat',
                'intern_missed_meetings',

                'talk_about_project_progress',
                'reviewed_original_timeline',

                'contribution_drafts',
                'contribution_review',
                'contribution_revised',

                'mentor_shares_positive_feedback',
                'mentor_promoting_work_to_community',
                'mentor_promoting_work_on_social_media',

                'intern_blogging',
                'mentor_discussing_blog',
                'mentor_promoting_blog_to_community',
                'mentor_promoting_blog_on_social_media',

                'mentor_introduced_intern_to_community',
                'intern_asks_questions_of_community_members',
                'intern_talks_to_community_members',
                'mentor_introduced_to_informal_chat_contacts',
                'intern_had_informal_chats',

                'mentor_support',
                'last_contact',
                'hours_worked',
                'time_comments',
                'progress_report',

                'recommend_open_source',
                'recommend_interning',
                'application_period_positive_impacts',
                'application_period_improvement_suggestions',
                'new_applicant_advice',
                'interning_positive_impacts',
                'interning_improvement_suggestions',
                'community_positive_impacts',
                'community_improvement_suggestions',
                'additional_feedback',
            ),
            field_classes = {
                'mentor_answers_questions': RadioBooleanField,
                'intern_asks_questions': RadioBooleanField,
                'mentor_support_when_stuck': RadioBooleanField,

                'daily_stand_ups': RadioBooleanField,
                'meets_privately': RadioBooleanField,
                'meets_over_phone_or_video_chat': RadioBooleanField,
                'intern_missed_meetings': RadioBooleanField,
                'talk_about_project_progress': RadioBooleanField,
                'reviewed_original_timeline': RadioBooleanField,

                'contribution_drafts': RadioBooleanField,
                'contribution_review': RadioBooleanField,
                'contribution_revised': RadioBooleanField,

                'mentor_shares_positive_feedback': RadioBooleanField,
                'mentor_promoting_work_to_community': RadioBooleanField,
                'mentor_promoting_work_on_social_media': RadioBooleanField,

                'intern_blogging': RadioBooleanField,
                'mentor_discussing_blog': RadioBooleanField,
                'mentor_promoting_blog_to_community': RadioBooleanField,
                'mentor_promoting_blog_on_social_media': RadioBooleanField,

                'mentor_introduced_intern_to_community': RadioBooleanField,
                'intern_asks_questions_of_community_members': RadioBooleanField,
                'intern_talks_to_community_members': RadioBooleanField,
                'mentor_introduced_to_informal_chat_contacts': RadioBooleanField,
                'intern_had_informal_chats': RadioBooleanField,
            },
    )

    def get_object(self):
        self.internship = intern_in_good_standing(self.request.user)
        if not self.internship:
            raise PermissionDenied("The account for {} is not associated with an intern in good standing".format(self.request.user.username))

        try:
            feedback = Feedback4FromIntern.objects.get(intern_selection=self.internship)
            if not feedback.can_edit():
                raise PermissionDenied("This feedback is already submitted and can't be updated right now.")
            return feedback
        except Feedback4FromIntern.DoesNotExist:
            return Feedback4FromIntern(intern_selection=self.internship)

    def get_context_data(self, **kwargs):
        context = super(Feedback4FromInternUpdate, self).get_context_data(**kwargs)
        context['internship'] = self.internship
        return context

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.allow_edits = False
        feedback.ip_address = self.request.META.get('REMOTE_ADDR')
        feedback.save()
        return redirect(reverse('dashboard') + '#feedback')

@login_required
@staff_member_required
def feedback_4_summary(request, round_slug):
    current_round = get_object_or_404(RoundPage, slug=round_slug)

    return render(request, 'home/feedback4.html',
            {
            'current_round' : current_round,
            },
            )

@login_required
@staff_member_required
def sponsor_info(request, round_slug):
    """
    Show sponsor names and amounts for each community.
    Display whether the sponsorship is confirmed or unconfirmed.
    Display community coordinator contact information needed
    to gather invoice information.
    """
    current_round = get_object_or_404(RoundPage, slug=round_slug)

    # Before new communities are approved,
    # it's helpful to know who is requesting Outreachy general funding.
    # Therefore, include both approved and pending communities.
    participations = Participation.objects.filter(
                models.Q(
                    approval_status=ApprovalStatus.APPROVED
                ) | models.Q(
                    approval_status=ApprovalStatus.PENDING
                ),
                participating_round=current_round,
            ).order_by('community__name')

    community_sponsors = [(p.community, p.sponsorship_set.all(), p.number_interns_approved(), p.number_interns_approved() * 6500) for p in participations]
    sponsors_alpha = Sponsorship.objects.filter(
                models.Q(
                    participation__approval_status=ApprovalStatus.APPROVED
                ) | models.Q(
                    participation__approval_status=ApprovalStatus.PENDING
                ),
                participation__participating_round=current_round,
            ).order_by('participation__community__name').order_by('name')

    return render(request, 'home/sponsor_info.html',
            {
            'current_round' : current_round,
            'community_sponsors' : community_sponsors,
            'sponsors_alpha' : sponsors_alpha,
            },
            )

@login_required
@staff_member_required
def sponsor_info_details(request, round_slug, community_slug):
    """
    Show sponsor details and sponsorship revision history for a particular community.
    """
    current_round = get_object_or_404(RoundPage, slug=round_slug)
    participation = get_object_or_404(Participation, participating_round=current_round, approval_status=ApprovalStatus.APPROVED, community__slug=community_slug)

    return render(request, 'home/sponsor_info_details.html',
            {
            'current_round' : current_round,
            'participation' : participation,
            'number_interns_approved' : participation.number_interns_approved(),
            'total_funding_needed' : participation.number_interns_approved() * 6500,
            'community' : participation.community,
            'sponsor_set' : participation.sponsorship_set.all(),
            },
            )

@login_required
@staff_member_required
def review_interns(request, round_slug):
    """
    Show information about applicants that are selected by mentors as interns.
    """
    current_round = get_object_or_404(RoundPage, slug=round_slug)
    intern_selections = InternSelection.objects.filter(applicant__application_round=current_round).order_by('project__project_round__community__name')

    return render(request, 'home/review_interns.html',
            {
            'current_round' : current_round,
            'intern_selections' : intern_selections,
            },
            )
class ReviewInterns(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/review_interns.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewInterns, self).get_context_data(**kwargs)
        current_round = get_object_or_404(
            RoundPage,
            slug=self.kwargs['round_slug'],
        )
        context['current_round'] = current_round
        context['role'] = Role(self.request.user, current_round)
        if not self.request.user.is_staff and not current_round.is_reviewer(self.request.user):
            raise PermissionDenied("You are not authorized to review applications.")

        context['intern_selections'] = InternSelection.objects.filter(applicant__application_round=current_round).order_by('project__project_round__community__name')
        return context

def alums_page(request, year=None, month=None):
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)
    visible_rounds = RoundPage.objects.filter(internannounce__lte=today)

    # Sorting the combined list in the database is hard to get right, but this
    # is a small list so it's fine to sort it in Python instead.
    start_dates = sorted(
        set(visible_rounds.values_list("internstarts", flat=True).order_by()).union(
            CohortPage.objects.values_list("round_start", flat=True).order_by()
        ),
        reverse=True,
    )

    if year is None or month is None:
        starts = start_dates[0]
        return redirect("cohort", year=starts.year, month=str(starts.month).rjust(2, "0"))

    try:
        round_page = visible_rounds.get(internstarts__year=year, internstarts__month=month)
        interns = Role(request.user, round_page).visible_intern_selections
        return render(request, 'home/alums_roundpage.html', {
            "start_dates": start_dates,
            "round": round_page,
            "interns": interns,
        })

    except RoundPage.DoesNotExist:
        # Check the historical records from before we had round pages:
        cohort_page = get_object_or_404(CohortPage, round_start__year=year, round_start__month=month)
        interns = cohort_page.participant.order_by('community', 'name')
        return render(request, 'home/alums_cohortpage.html', {
            "start_dates": start_dates,
            "cohort": cohort_page,
            "interns": interns,
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
        past_interns_opt_out = [p for p in past_interns if p.survey_opt_out or p.project.round().internends >= date.today()]
        past_interns = [p for p in past_interns if not p.survey_opt_out and p.project.round().internends >= date.today()]

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
        return redirect('dashboard')

@login_required
def applicant_review_summary(request, status, owner_username=None, review_status=None, rating=None, process=False):
    """
    For applicant reviewers and staff, show the status of applications that
    have the specified approval status.
    """
    # Update dashboard.application_summary too if you change anything here.

    current_round = get_current_round_for_initial_application_review()

    if not request.user.is_staff and not current_round.is_reviewer(request.user):
        raise PermissionDenied("You are not authorized to review applications.")

    if owner_username and owner_username != 'all':
        try:
            comrade = Comrade.objects.get(account__username=owner_username)
        except Comrade.DoesNotExist:
            raise PermissionDenied("No such applicant reviewer")

    applications = ApplicantApproval.objects.filter(
        application_round=current_round,
        approval_status=status,
    ).order_by('pk').select_related(
        'applicant__account',
        # one-to-one reverse references:
        'workeligibility',
        'priorfossexperience',
        'timecommitmentsummary',
    ).prefetch_related(
        # many-to-many relations:
        'essay_qualities',
        # small number of owners shared across many applicants:
        'review_owner__comrade',
    )
    # XXX: This will break if anyone has a username of all - not sure how to handle this
    if owner_username and owner_username != 'all':
        applications = applications.filter(review_owner__comrade__account__username=owner_username)
    elif not owner_username:
        # look for unowned applications
        applications = applications.filter(review_owner=None)
    # else don't filter on application ownership

    if review_status == 'unreviewed':
        applications = applications.filter(initialapplicationreview__isnull=True)
    elif review_status == 'unreviewed-non-student':
        applications = applications.filter(initialapplicationreview__isnull=True).filter(schoolinformation__isnull=True)
    elif review_status == 'reviewed':
        applications = applications.filter(initialapplicationreview__isnull=False)
    # else don't filter on review status

    if rating:
        applications = applications.filter(initialapplicationreview__essay_rating=rating)

    applications = applications.distinct()

    paginator = Paginator(applications, 25)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.page(page_number)

    if status == ApprovalStatus.PENDING:
        heading = 'Pending Applications'
    elif status == ApprovalStatus.REJECTED:
        heading = 'Rejected Applications'
    elif status == ApprovalStatus.APPROVED:
        heading = 'Approved Applications'
    if owner_username and owner_username != 'all':
        heading = heading + ' - owned by {}'.format(comrade.public_name)

    if process:
        return render(request, 'home/process_initial_applications_summary.html', {
            "applications": page_obj,
            "heading": heading,
        })

    return render(request, 'home/applicant_review_summary.html', {
        "applications": page_obj,
        "heading": heading,
    })

# Passed action, applicant_username
class ApplicantApprovalUpdate(ApprovalStatusAction):
    model = ApplicantApproval

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()
        return get_object_or_404(ApplicantApproval,
                applicant__account__username=self.kwargs['applicant_username'],
                application_round=current_round)

    def get_success_url(self):
        # If the ApplicantApproval was just rejected
        # collect aggregate anonymized statistics and delete:
        # - essay answers
        # - gender identity data
        # - race and ethnicity demographics
        if self.object.approval_status == ApprovalStatus.REJECTED:
            self.object.collect_statistics()
            self.object.purge_sensitive_data()

        # Outreachy organizers will manually collect statistics
        # and purge essays of approved applications

        return self.object.get_preview_url()

class DeleteApplication(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        # Only allow staff to delete initial applications
        if not request.user.is_staff:
            raise PermissionDenied("Only Outreachy organizers can delete initial applications.")

        # This only happens during review, but only makes sense to do while the
        # applicant still has an opportunity to submit the initial application
        # again, so we don't use the longer review period here.
        current_round = get_current_round_for_initial_application()

        application = get_object_or_404(ApplicantApproval,
                applicant__account__username=self.kwargs['applicant_username'],
                application_round=current_round)
        application.delete()

        # We need to delete both pending and rejected applications,
        # so I'm not sure which to redirect to.
        return redirect('dashboard')

class NotifyEssayNeedsUpdating(LoginRequiredMixin, ComradeRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        current_round = get_current_round_for_initial_application_review()
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
        return redirect(essay.applicant.get_preview_url())

class BarriersToParticipationUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    model = BarriersToParticipation

    fields = [
            'underrepresentation',
            'employment_bias',
            'lacking_representation',
            'systemic_bias',
            ]

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()
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
        current_round = get_current_round_for_initial_application_review()
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
        return redirect(school_info.applicant.get_preview_url())

class SchoolInformationUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    model = SchoolInformation

    fields = [
            'current_academic_calendar',
            'next_academic_calendar',
            'school_term_updates',
            ]

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()
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
    current_round = get_current_round_for_initial_application_review()

    try:
        reviewer = current_round.applicationreviewer_set.approved().get(
            comrade__account=self.request.user,
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
            reviewer = get_object_or_404(
                application.application_round.applicationreviewer_set.approved(),
                comrade__account__username=self.kwargs['owner'],
            )

        application.review_owner = reviewer
        application.save()

        return redirect(self.request.GET.get('next', application.get_preview_url()))

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
        elif rating == "NOTCOMPELLING":
            review.essay_rating = review.NOTCOMPELLING
        elif rating == "NOTUNDERSTOOD":
            review.essay_rating = review.NOTUNDERSTOOD
        elif rating == "SPAM":
            review.essay_rating = review.SPAM
        review.save()

        return redirect(self.request.GET.get('next', application.get_preview_url()))

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

        return redirect(application.get_preview_url())

class ReviewEssay(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    template_name = 'home/review_essay.html'

    form_class = modelform_factory(
        ApplicantApproval,
        fields = [
            'essay_qualities',
        ],
        widgets = {
            'essay_qualities': widgets.CheckboxSelectMultiple,
        },
    )

    def get_object(self):
        current_round = get_current_round_for_initial_application_review()

        application = get_object_or_404(ApplicantApproval,
                applicant__account__username=self.kwargs['applicant_username'],
                application_round=current_round)
        try:
            reviewer = application.application_round.applicationreviewer_set.approved().get(
                comrade__account=self.request.user,
            )
        except ApplicationReviewer.DoesNotExist:
            raise PermissionDenied("You are not currently an approved application reviewer.")

        return application

    def get_success_url(self):
        return self.object.get_preview_url()

class ReviewCommentUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    model = InitialApplicationReview
    fields = ['comments',]

    def get_object(self):
        application, reviewer, review = get_or_create_application_reviewer_and_review(self)
        return review

    def get_success_url(self):
        return self.request.GET.get('next', self.object.application.get_preview_url())

@login_required
def internship_cohort_statistics(request):
    """
    For Outreachy staff, show statistics about applicants and interns.
    """

    if not request.user.is_staff:
        raise PermissionDenied("You are not authorized to view internship cohort statistics.")

    rounds = RoundPage.objects.all().order_by('-internstarts')
    return render(request, 'home/internship_cohort_statistics.html', {
        'rounds': rounds,
        })

def docs_toc(request):
    return render(request, 'home/docs/toc.html')

def docs_applicant(request):
    current_round = RoundPage.objects.latest('internannounce')
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)
    try:
        previous_round = RoundPage.objects.filter(
            contributions_open__lte=today,
        ).latest('internstarts')
        previous_round.today = today
    except RoundPage.DoesNotExist:
        previous_round = None

    return render(request, 'home/docs/applicant_guide.html', {
        'current_round': current_round,
        'previous_round': previous_round,
        })

def docs_community(request):
    current_round = RoundPage.objects.latest('internannounce')
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)
    five_weeks_from_now = today + timedelta(weeks=5)
    try:
        previous_round = RoundPage.objects.filter(
            internends__lte=five_weeks_from_now,
        ).latest('internstarts')
        previous_round.today = today
    except RoundPage.DoesNotExist:
        previous_round = None

    return render(request, 'home/docs/community_guide.html', {
        'current_round': current_round,
        'previous_round': previous_round,
        })

def docs_internship(request):
    now = datetime.now(timezone.utc)
    today = get_deadline_date_for(now)
    five_weeks_ago = today - timedelta(days=7*5)

    try:
        applicant_round = RoundPage.objects.get(
            pingnew__lte=today,
            internannounce__gt=today,
        )
    except RoundPage.DoesNotExist:
        applicant_round = None

    try:
        intern_round = RoundPage.objects.get(
            internannounce__lte=today,
            internends__gt=five_weeks_ago,
        )
    except RoundPage.DoesNotExist:
        intern_round = None

    return render(request, 'home/docs/internship_guide.html', {
        'applicant_round': applicant_round,
        'intern_round': intern_round,
        })

class InformalChatContacts(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/informal_chat_contacts.html'

    def get_context_data(self, **kwargs):
        # Who can view this page:
        #  - APPROVED - Intern logged in, who is in good standing
        #  - APPROVED - Alum logged in, who is in good standing
        #  - APPROVED - Mentor logged in, who is a mentor of an intern in good standing
        #  - APPROVED - Approved coordinator logged in, whose community has been approved to participate
        #  - APPROVED - Staff
        comrade = self.request.user.comrade

        #  - APPROVED - Intern logged in, who is in good standing
        #  - APPROVED - Alum logged in, who is in good standing
        # This selects both current interns and alums
        # Note: this is a filter instead of a get because we have had interns do an internship twice
        # e.g. because they had to quit their first internship due to medical reasons.
        intern_selections = InternSelection.objects.filter(
                applicant__applicant=comrade,
                organizer_approved=True,
                in_good_standing=True,
                )

        if not intern_selections:
            #  - APPROVED - Mentor logged in, who is a mentor of an intern in good standing
            # Check for an approved project with a community approved to participate
            mentor_relationships = MentorRelationship.objects.filter(
                    mentor__mentor=comrade,
                    mentor__approval_status=ApprovalStatus.APPROVED,
                    intern_selection__project__approval_status=ApprovalStatus.APPROVED,
                    intern_selection__project__project_round__approval_status=ApprovalStatus.APPROVED,
                    intern_selection__organizer_approved=True,
                    intern_selection__in_good_standing=True,
                    )

            #  - APPROVED - Approved coordinator logged in, whose community has been approved to participate
            if not mentor_relationships:
                coordinator_approvals = CoordinatorApproval.objects.filter(
                        coordinator=comrade,
                        approval_status=ApprovalStatus.APPROVED,
                        community__participation__approval_status=ApprovalStatus.APPROVED,
                        )
                if not coordinator_approvals:
                    #  - APPROVED - Staff
                    if not comrade.account.is_staff:
                        raise PermissionDenied('Permission denied: You must be logged in to see the informal chat contacts. Contacts are only available to Outreachy interns and alums who are in good standing, and their mentors and coordinators.')

        # get active informal chat contacts
        contacts = InformalChatContact.objects.filter(active=True).order_by('name')

        context = super(InformalChatContacts, self).get_context_data(**kwargs)
        context.update({
            'contacts' : contacts,
            })
        return context


def donate(request):
    return render(request, 'home/donate.html')

def sponsor(request):
    return render(request, 'home/sponsor.html', {
        'current_round': get_current_round_for_sponsors(),
        })

def opportunities(request):
    return render(request, 'home/opportunities.html')

def community_participation_rules(request):
    return render(request, 'home/community_participation_rules.html')

@login_required
def dashboard(request):
    return render(request, 'home/dashboard.html', {
        'sections': get_dashboard_sections(request),
    })
