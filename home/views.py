from betterforms.multiform import MultiModelForm
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import inlineformset_factory, ModelForm, modelform_factory, ValidationError, widgets
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import FormView, View, DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from formtools.wizard.views import SessionWizardView
from itertools import chain, groupby
from markdownx.utils import markdownify
from registration.backends.hmac import views as hmac_views
import reversion

from . import email

from .mixins import ApprovalStatusAction
from .mixins import ComradeRequiredMixin
from .mixins import EligibleApplicantRequiredMixin
from .mixins import Preview

from .models import ApplicantApproval
from .models import ApprovalStatus
from .models import CommunicationChannel
from .models import Community
from .models import Comrade
from .models import ContractorInformation
from .models import Contribution
from .models import CoordinatorApproval
from .models import create_time_commitment_calendar
from .models import DASHBOARD_MODELS
from .models import EmploymentTimeCommitment
from .models import FinalApplication
from .models import InternSelection
from .models import has_deadline_passed
from .models import MentorApproval
from .models import MentorRelationship
from .models import NewCommunity
from .models import NonCollegeSchoolTimeCommitment
from .models import Notification
from .models import Participation
from .models import Project
from .models import ProjectSkill
from .models import RoundPage
from .models import SchoolInformation
from .models import SchoolTimeCommitment
from .models import SignedContract
from .models import Sponsorship
from .models import VolunteerTimeCommitment

from os import path

class RegisterUser(hmac_views.RegistrationView):

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
    model = Comrade

    # FIXME - we need a way for comrades to change their passwords
    # and update and re-verify their email address.
    fields = [
            'public_name',
            'nick_name',
            'legal_name',
            'pronouns',
            'pronouns_to_participants',
            'pronouns_public',
            'timezone',
            'location',
            'nick',
            'github_url',
            'gitlab_url',
            'blog_url',
            'blog_rss_url',
            'twitter_url',
            'agreed_to_code_of_conduct',
            ]

    # FIXME - we need to migrate any existing staff users who aren't a Comrade
    # to the Comrade model instead of the User model.
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

BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))

def general_info_is_approved(wizard):
    cleaned_data = wizard.get_cleaned_data_for_step('General Info')
    if not cleaned_data:
        return True
    if not cleaned_data['over_18']:
        return False
    if cleaned_data['gsoc_or_outreachy_internship']:
        return False
    if not cleaned_data['eligible_to_work']:
        return False
    if cleaned_data['under_export_control']:
        return False
    # If they're in a us_sanctioned_country, go ahead and collect the
    # rest of the information on the forms, but we'll mark them as
    # PENDING later.
    return True

def show_us_demographics(wizard):
    if not general_info_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('General Info') or {}
    if not cleaned_data:
        return True
    us_resident = cleaned_data.get('us_national_or_permanent_resident', True)
    living_in_us = cleaned_data.get('living_in_us', True)
    return us_resident or living_in_us

def gender_and_demographics_is_approved(wizard):
    if not general_info_is_approved(wizard):
        return False
    demo_data = wizard.get_cleaned_data_for_step('USA demographics')
    if demo_data and demo_data['us_resident_demographics'] is True:
        return True

    gender_data = wizard.get_cleaned_data_for_step('Gender Identity')
    if not gender_data:
        return True

    gender_minority_list = [
            'transgender',
            'genderqueer',
            'woman',
            'demi_boy',
            'demi_girl',
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
            # Collect information for someone who doesn't specify their gender
            # then ask them to send an email to the Outreachy organizers
            'prefer_not_to_say',
            ]
    return any(gender_data[x] for x in gender_minority_list) or gender_data['self_identify'] != ''

def show_noncollege_school_info(wizard):
    if not gender_and_demographics_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('enrolled_as_noncollege_student', True)

def show_school_info(wizard):
    if not gender_and_demographics_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('enrolled_as_student', True)

def show_contractor_info(wizard):
    if not gender_and_demographics_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('contractor', True)

def show_employment_info(wizard):
    if not gender_and_demographics_is_approved(wizard):
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
    if not gender_and_demographics_is_approved(wizard):
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

    ctcs = [ time_commitment(d, d['hours_per_week'])
            for d in wizard.get_cleaned_data_for_step('Coding School or Online Courses Time Commitment Info') or []
            if d ]

    etcs = [ time_commitment(d, 0 if d['quit_on_acceptance'] else d['hours_per_week'])
            for d in wizard.get_cleaned_data_for_step('Employment Info') or []
            if d ]

    stcs = [ time_commitment(d, 40 * ((d['registered_credits'] - d['outreachy_credits'] - d['thesis_credits']) / d['typical_credits']))
            for d in wizard.get_cleaned_data_for_step('School Term Info') or []
            if d ]

    required_free_days = 7*7
    calendar = create_time_commitment_calendar(chain(tcs, ctcs, etcs, stcs), application_round)

    for key, group in groupby(calendar, lambda hours: hours <= 20):
        if key is True and len(list(group)) >= required_free_days:
            return True
    return False

def determine_eligibility(wizard, application_round):
    if not (general_info_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'GENERAL')
    if not (gender_and_demographics_is_approved(wizard)):
        return (ApprovalStatus.REJECTED, 'DEMOGRAPHICS')

    if not time_commitments_are_approved(wizard, application_round):
        return (ApprovalStatus.REJECTED, 'TIME')

    general_data = wizard.get_cleaned_data_for_step('General Info')
    gender_data = wizard.get_cleaned_data_for_step('Gender Identity')

    if general_data['us_sanctioned_country']:
        return (ApprovalStatus.PENDING, '')

    demo_data = wizard.get_cleaned_data_for_step('USA demographics')
    if not (demo_data and demo_data['us_resident_demographics']):
        if gender_data['prefer_not_to_say'] or gender_data['self_identify']:
            return (ApprovalStatus.PENDING, '')

    return (ApprovalStatus.APPROVED, '')

class EligibilityUpdateView(LoginRequiredMixin, ComradeRequiredMixin, reversion.views.RevisionMixin, SessionWizardView):
    template_name = 'home/wizard_form.html'
    condition_dict = {
            'USA demographics': show_us_demographics,
            'Gender Identity': general_info_is_approved,
            'Time Commitments': gender_and_demographics_is_approved,
            'School Info': show_school_info,
            'School Term Info': show_school_info,
            'Coding School or Online Courses Time Commitment Info': show_noncollege_school_info,
            'Contractor Info': show_contractor_info,
            'Employment Info': show_employment_info,
            'Volunteer Time Commitment Info': show_time_commitment_info,
            }
    form_list = [
            ('General Info', modelform_factory(ApplicantApproval, fields=(
                'over_18',
                'eligible_to_work',
                'gsoc_or_outreachy_internship',
                'us_national_or_permanent_resident',
                'living_in_us',
                'under_export_control',
                'us_sanctioned_country',
                ),
                # FIXME: this allows people to submit a partial form
                # without validating either 'yes' or 'no' is selected
                widgets = {
                    'over_18': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'gsoc_or_outreachy_internship': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'eligible_to_work': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'us_national_or_permanent_resident': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'living_in_us': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'under_export_control': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'us_sanctioned_country': widgets.RadioSelect(choices=BOOL_CHOICES),
                    },
                )),
            ('USA demographics', modelform_factory(ApplicantApproval, fields=(
                'us_resident_demographics',
                ),
                widgets = {
                    'us_resident_demographics': widgets.RadioSelect(choices=BOOL_CHOICES),
                    },
                )),
            ('Gender Identity', modelform_factory(ApplicantApproval, fields=(
                'transgender',
                'genderqueer',
                'man',
                'woman',
                'demi_boy',
                'demi_girl',
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
                widgets = {
                    'transgender': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'genderqueer': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'man': widgets.CheckboxInput(),
                    'woman': widgets.CheckboxInput(),
                    'demi_boy': widgets.CheckboxInput(),
                    'demi_girl': widgets.CheckboxInput(),
                    'non_binary': widgets.CheckboxInput(),
                    'demi_non_binary': widgets.CheckboxInput(),
                    'genderflux': widgets.CheckboxInput(),
                    'genderfluid': widgets.CheckboxInput(),
                    'demi_genderfluid': widgets.CheckboxInput(),
                    'demi_gender': widgets.CheckboxInput(),
                    'bi_gender': widgets.CheckboxInput(),
                    'tri_gender': widgets.CheckboxInput(),
                    'multigender': widgets.CheckboxInput(),
                    'pangender': widgets.CheckboxInput(),
                    'maxigender': widgets.CheckboxInput(),
                    'aporagender': widgets.CheckboxInput(),
                    'intergender': widgets.CheckboxInput(),
                    'mavrique': widgets.CheckboxInput(),
                    'gender_confusion': widgets.CheckboxInput(),
                    'gender_indifferent': widgets.CheckboxInput(),
                    'graygender': widgets.CheckboxInput(),
                    'agender': widgets.CheckboxInput(),
                    'genderless': widgets.CheckboxInput(),
                    'gender_neutral': widgets.CheckboxInput(),
                    'neutrois': widgets.CheckboxInput(),
                    'androgynous': widgets.CheckboxInput(),
                    'androgyne': widgets.CheckboxInput(),
                    'prefer_not_to_say': widgets.CheckboxInput(),
                    },
                )),
            ('Time Commitments', modelform_factory(ApplicantApproval, fields=(
                'enrolled_as_student',
                'enrolled_as_noncollege_student',
                'employed',
                'contractor',
                'volunteer_time_commitments',
                ),
                widgets = {
                    'enrolled_as_student': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'enrolled_as_noncollege_student': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'employed': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'contractor': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'volunteer_time_commitments': widgets.RadioSelect(choices=BOOL_CHOICES),
                    },
                )),
            ('School Info', inlineformset_factory(ApplicantApproval,
                SchoolInformation,
                min_num=1,
                max_num=1,
                validate_min=True,
                validate_max=True,
                can_delete=False,
                fields=(
                    'university_name',
                    'university_website',
                    'degree_name',
                ))),
            ('School Term Info', inlineformset_factory(ApplicantApproval,
                SchoolTimeCommitment,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'term_name',
                    'start_date',
                    'end_date',
                    'typical_credits',
                    'registered_credits',
                    'outreachy_credits',
                    'thesis_credits',
                ),
                widgets = {
                    },
                )),
            ('Coding School or Online Courses Time Commitment Info', inlineformset_factory(ApplicantApproval,
                NonCollegeSchoolTimeCommitment,
                min_num=1,
                validate_min=True,
                extra=4,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'description',
                ))),
            ('Contractor Info', inlineformset_factory(ApplicantApproval,
                ContractorInformation,
                min_num=1,
                max_num=1,
                validate_min=True,
                validate_max=True,
                can_delete=False,
                fields=(
                    'typical_hours',
                    'continuing_contract_work',
                ),
                widgets = {
                    'continuing_contract_work': widgets.RadioSelect(choices=BOOL_CHOICES),
                    },
                )),
            ('Employment Info', inlineformset_factory(ApplicantApproval,
                EmploymentTimeCommitment,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'quit_on_acceptance',
                ),
                widgets = {
                    'quit_on_acceptance': widgets.CheckboxInput(),
                    },
                )),
            ('Volunteer Time Commitment Info', inlineformset_factory(ApplicantApproval,
                VolunteerTimeCommitment,
                min_num=1,
                validate_min=True,
                extra=2,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                    'description',
                ))),
            ]
    # TODO: override get method to redirect to results page if the person
    # has filled out an application
    TEMPLATES = {
            'General Info': 'home/eligibility_wizard_general.html',
            'USA demographics': 'home/eligibility_wizard_us_demographics.html',
            'Gender Identity': 'home/eligibility_wizard_gender.html',
            'Time Commitments': 'home/eligibility_wizard_time_commitments.html',
            'School Info': 'home/eligibility_wizard_school_info.html',
            'School Term Info': 'home/eligibility_wizard_school_terms.html',
            'Coding School or Online Courses Time Commitment Info': 'home/eligibility_wizard_noncollege_school_info.html',
            'Contractor Info': 'home/eligibility_wizard_contractor_info.html',
            'Employment Info': 'home/eligibility_wizard_employment_info.html',
            'Volunteer Time Commitment Info': 'home/eligibility_wizard_time_commitment_info.html',
            }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_instance(self, step):
        current_round = RoundPage.objects.latest('internstarts')
        if current_round.has_late_application_deadline_passed():
            raise PermissionDenied('The Outreachy application period is closed. If you are an applicant who has submitted an application for an internship project and your time commitments have increased, please contact the Outreachy organizers (see contact link above). Eligibility checking will become available shortly before the next application period opens. Please sign up for the announcements mailing list for an email when the next application period opens: https://lists.outreachy.org/cgi-bin/mailman/listinfo/announce')

        # This implementation ignores `step` which is fine as long as
        # all of the forms are supposed to edit the same base object and
        # are either ModelForm or InlineModelForm.

        # Make sure to use the same Python object for all steps, rather
        # than constructing a different empty object for each step, by
        # caching it on this view instance.
        if not getattr(self, 'object', None):
            try:
                self.object = ApplicantApproval.objects.get(
                        applicant=self.request.user.comrade,
                        application_round=current_round)
            except ApplicantApproval.DoesNotExist:
                self.object = ApplicantApproval(
                        applicant=self.request.user.comrade,
                        application_round=current_round)
        return self.object

    def get_context_data(self, **kwargs):
        context = super(EligibilityUpdateView, self).get_context_data(**kwargs)
        context['current_round'] = self.object.application_round
        return context

    def done(self, form_list, **kwargs):
        # We have multiple forms editing the same object, but we want to
        # batch up the database writes so the object is only actually
        # updated once.

        inlines = []
        for form in form_list:
            if isinstance(form, BaseInlineFormSet):
                inlines.append(form)
            else:
                # Assume (and assert) that any form which is not an
                # InlineFormSet must be a ModelForm that edits
                # self.object.
                result = form.save(commit=False)
                assert result == self.object

        # At this point we've saved (but not committed) all the forms
        # that edit self.object.

        self.object.approval_status, self.object.reason_denied = determine_eligibility(self, self.object.application_round)

        # Make sure to commit the object to the database before saving
        # any of the InlineFormSets, so they can set their foreign keys
        # to point to this object.
        self.object.save()

        for inlineformset in inlines:
            inlineformset.save()

        if self.object.approval_status == ApprovalStatus.PENDING:
            email.approval_status_changed(self.object, self.request)

        return redirect(self.request.GET.get('next', reverse('eligibility-results')))

class EligibilityResults(LoginRequiredMixin, ComradeRequiredMixin, DetailView):
    template_name = 'home/eligibility_results.html'
    context_object_name = 'application'

    def get_object(self):
        current_round = RoundPage.objects.latest('internstarts')
        return get_object_or_404(ApplicantApproval,
                    applicant=self.request.user.comrade,
                    application_round=current_round)

    def get_context_data(self, **kwargs):
        context = super(EligibilityResults, self).get_context_data(**kwargs)
        context.update(self.object.get_time_commitments())
        context['current_round'] = self.object.application_round
        return context

def current_round_page(request):
    current_round = RoundPage.objects.latest('internstarts')
    approved_participations = current_round.participation_set.approved().order_by('community__name')

    closed_approved_projects = []
    ontime_approved_projects = []
    late_approved_projects = []
    for p in approved_participations:
        projects = p.project_set.approved().filter(deadline=Project.CLOSED,
                approval_status=ApprovalStatus.APPROVED)
        if projects:
            closed_approved_projects.append((p.community, projects))
        projects = p.project_set.approved().filter(deadline=Project.ONTIME,
                approval_status=ApprovalStatus.APPROVED)
        if projects:
            ontime_approved_projects.append((p.community, projects))
        projects = p.project_set.approved().filter(deadline=Project.LATE,
                approval_status=ApprovalStatus.APPROVED)
        if projects:
            late_approved_projects.append((p.community, projects))
    example_skill = ProjectSkill

    return render(request, 'home/round_page_with_communities.html',
            {
            'current_round' : current_round,
            'closed_projects': closed_approved_projects,
            'ontime_projects': ontime_approved_projects,
            'late_projects': late_approved_projects,
            'example_skill': example_skill,
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
    # FIXME: Grab data to display about communities and substitute into the template
    # Grab the most current round, based on the internship start date.
    # See https://docs.djangoproject.com/en/1.11/ref/models/querysets/#latest
    current_round = RoundPage.objects.latest('internstarts')

    # Now grab the community IDs of all communities participating in the current round
    # https://docs.djangoproject.com/en/1.11/topics/db/queries/#following-relationships-backward
    # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values-list
    # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#values
    participating_communities = {
            p.community_id: p
            for p in current_round.participation_set.all()
            }
    all_communities = Community.objects.all().order_by('name')
    approved_communities = []
    pending_communities = []
    rejected_communities = []
    not_participating_communities = []
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
    current_round = RoundPage.objects.latest('internstarts')
    community = get_object_or_404(Community, slug=community_slug)

    coordinator = None
    notification = None
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
            notification = Notification.objects.get(comrade__account=request.user, community=community)
        except Notification.DoesNotExist:
            pass

    context = {
            'current_round' : current_round,
            'community': community,
            'coordinator': coordinator,
            'notification': notification,
            }

    # Try to see if this community is participating in the current round
    # and get the Participation object if so.
    try:
        context['participation_info'] = Participation.objects.get(community=community, participating_round=current_round)
    except Participation.DoesNotExist:
        pass

    return render(request, 'home/community_read_only.html', context)

# A Comrade wants to sign up to be notified when a community coordinator
# says this community is participating in a new round
# FIXME we need to deal with deleting these once a community signs up.
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

def community_landing_view(request, round_slug, slug):
    # Try to see if this community is participating in that round
    # and if so, get the Participation object and related objects.
    participation_info = get_object_or_404(
            Participation.objects.select_related('community', 'participating_round'),
            community__slug=slug,
            participating_round__slug=round_slug,
            )
    projects = get_list_or_404(participation_info.project_set.approved())
    ontime_projects = [p for p in projects if p.deadline == Project.ONTIME]
    late_projects = [p for p in projects if p.deadline == Project.LATE]
    closed_projects = [p for p in projects if p.deadline == Project.CLOSED]
    example_skill = ProjectSkill
    if request.user.is_authenticated:
        try:
            # Although the current user is authenticated, don't assume
            # that they have a Comrade instance. Instead check that the
            # approval's coordinator is attached to a User that matches
            # this one.
            approved_coordinator_list = participation_info.community.coordinatorapproval_set.filter(
                    approval_status=ApprovalStatus.APPROVED)
        except CoordinatorApproval.DoesNotExist:
            approved_coordinator_list = None
    else:
            approved_coordinator_list = None

    return render(request, 'home/community_landing.html',
            {
            'participation_info': participation_info,
            'ontime_projects': ontime_projects,
            'late_projects': late_projects,
            'closed_projects': closed_projects,
            # TODO: make the template get these off the participation_info instead of passing them in the context
            'current_round' : participation_info.participating_round,
            'community': participation_info.community,
            'approved_coordinator_list': approved_coordinator_list,
            'example_skill': example_skill,
            },
            )

class CommunityCreate(LoginRequiredMixin, ComradeRequiredMixin, CreateView):
    model = NewCommunity
    fields = ['name', 'description', 'long_description', 'website',
            'community_size', 'longevity', 'participating_orgs',
            'approved_license', 'unapproved_license_description',
            'no_proprietary_software', 'proprietary_software_description',
            'goverance', 'code_of_conduct', 'cla', 'dco']

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
        return redirect(Participation(community=self.object).get_action_url('submit'))

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
        participating_round = RoundPage.objects.latest('internstarts')
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
def project_read_only_view(request, community_slug, project_slug):
    current_round = RoundPage.objects.latest('internstarts')
    project = get_object_or_404(
            Project.objects.select_related('project_round__participating_round', 'project_round__community'),
            slug=project_slug,
            project_round__participating_round=current_round,
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
            'mentored_before',
            'mentorship_style',
            'longevity',
            'mentor_foss_contributions',
            'communication_channel_username',
            'instructions_read',
            'understands_intern_time_commitment',
            'understands_applicant_time_commitment',
            'understands_mentor_contract',
            ]

    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        project = get_object_or_404(Project,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=participating_round,
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
                'community_slug': self.object.project.project_round.community.slug,
                'project_slug': self.object.project.slug,
                })

        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status != self.target_status:
            email.approval_status_changed(self.object, self.request)

class ProjectAction(ApprovalStatusAction):
    fields = ['short_title', 'approved_license', 'unapproved_license_description', 'no_proprietary_software', 'proprietary_software_description', 'longevity', 'community_size', 'community_benefits', 'intern_tasks', 'intern_benefits', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'contribution_tasks', 'long_description', 'deadline', 'needs_more_applicants']

    # Make sure that someone can't feed us a bad community URL by fetching the Community.
    def get_object(self):
        participating_round = RoundPage.objects.latest('internstarts')
        participation = get_object_or_404(Participation,
                    community__slug=self.kwargs['community_slug'],
                    participating_round=participating_round)

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
        participating_round = RoundPage.objects.latest('internstarts')
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=participating_round)
        if not project.is_submitter(self.request.user):
            return redirect(project.get_preview_url())
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
        current_round = RoundPage.objects.latest('internstarts')
        return get_object_or_404(
                MentorApproval,
                project__slug=self.kwargs['project_slug'],
                project__project_round__participating_round=current_round,
                project__project_round__community__slug=self.kwargs['community_slug'],
                mentor__account__username=self.kwargs['username'])

class CoordinatorApprovalPreview(Preview):
    def get_object(self):
        return get_object_or_404(
                CoordinatorApproval,
                community__slug=self.kwargs['community_slug'],
                coordinator__account__username=self.kwargs['username'])

class MentorCheckDeadlinesReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/mentor_deadline_reminder.html'

    def get_context_data(self, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        projects = Project.objects.filter(
                approval_status__in=[Project.APPROVED, Project.PENDING],
                project_round__participating_round=current_round)
        context = super(MentorCheckDeadlinesReminder, self).get_context_data(**kwargs)
        context.update({
            'projects': projects,
            })
        return context

    def post(self, request, *args, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        projects = Project.objects.filter(
                approval_status__in=[Project.APPROVED, Project.PENDING],
                project_round__participating_round=current_round)
        for p in projects:
            email.project_applicant_review(p, self.request)
        return redirect(reverse('dashboard'))

def get_open_approved_projects(current_round):
    if not current_round.has_ontime_application_deadline_passed():
        return Project.objects.filter(
                project_round__participating_round=current_round).all().approved()
    elif not current_round.has_late_application_deadline_passed():
        return Project.objects.filter(
                deadline=Project.LATE,
                project_round__participating_round=current_round).all().approved()
    return None

def get_closed_approved_projects(current_round):
    if current_round.has_ontime_application_deadline_passed():
        return Project.objects.filter(
                project_round__participating_round=current_round,
                deadline__in=[Project.ONTIME, Project.CLOSED]).all().approved()
    elif current_round.has_late_application_deadline_passed():
        return Project.objects.filter(
                deadline=Project.LATE,
                project_round__participating_round=current_round).all().approved()
    return None

class MentorApplicationDeadlinesReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/mentor_deadline_application_reminder.html'

    def get_context_data(self, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        context = super(MentorApplicationDeadlinesReminder, self).get_context_data(**kwargs)
        context.update({
            'projects': get_open_approved_projects(current_round),
            })
        return context

    def post(self, request, *args, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        projects = get_open_approved_projects(current_round)
        for p in projects:
            email.mentor_application_deadline_reminder(p, self.request)
        return redirect(reverse('dashboard'))

class MentorInternSelectionReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/mentor_intern_selection_reminder.html'

    def get_context_data(self, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        context = super(MentorInternSelectionReminder, self).get_context_data(**kwargs)
        context.update({
            'projects': get_closed_approved_projects(current_round),
            })
        return context

    def post(self, request, *args, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        projects = get_closed_approved_projects(current_round)
        for p in projects:
            email.mentor_intern_selection_reminder(p, self.request)
        return redirect(reverse('dashboard'))

class CoordinatorInternSelectionReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/coordinator_intern_selection_reminder.html'

    def get_context_data(self, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        context = super(CoordinatorInternSelectionReminder, self).get_context_data(**kwargs)
        participations = Participation.objects.filter(
                participating_round=current_round,
                approval_status=Participation.APPROVED)
        context.update({
            'participations': participations,
            })
        return context

    def post(self, request, *args, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        participations = Participation.objects.filter(
                participating_round=current_round,
                approval_status=Participation.APPROVED)
        for p in participations:
            email.coordinator_intern_selection_reminder(p, self.request)
        return redirect(reverse('dashboard'))

class ApplicantsDeadlinesReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/applicants_deadline_reminder.html'

    def get_context_data(self, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        late_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.LATE)
        promoted_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.ONTIME,
                needs_more_applicants=True)
        closed_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.CLOSED)
        context = super(ApplicantsDeadlinesReminder, self).get_context_data(**kwargs)
        context.update({
            'current_round': current_round,
            'late_projects': late_projects,
            'promoted_projects': promoted_projects,
            'closed_projects': closed_projects,
            })
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        late_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.LATE)
        promoted_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.ONTIME,
                needs_more_applicants=True)
        closed_projects = Project.objects.filter(
                project_round__participating_round=current_round,
                approval_status=Project.APPROVED,
                deadline=Project.CLOSED)
        email.applicant_deadline_reminder(late_projects, promoted_projects, closed_projects, current_round, self.request)
        return redirect(reverse('dashboard'))

def get_contributors_with_upcoming_deadlines():
    current_round = RoundPage.objects.latest('internstarts')
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
    return None

class ContributorsApplicationPeriodEndedReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/contributors_application_period_ended.html'

    def get_context_data(self, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        contributors = Comrade.objects.filter(
                applicantapproval__application_round=current_round,
                applicantapproval__approval_status=ApprovalStatus.APPROVED,
                applicantapproval__contribution__isnull=False).distinct()

        context = super(ContributorsApplicationPeriodEndedReminder, self).get_context_data(**kwargs)
        context.update({
            'current_round': current_round,
            'contributors': contributors,
            })
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        contributors = Comrade.objects.filter(
                applicantapproval__application_round=current_round,
                applicantapproval__approval_status=ApprovalStatus.APPROVED,
                applicantapproval__contribution__isnull=False).distinct()

        for c in contributors:
            email.contributor_application_period_ended(
                    c,
                    current_round,
                    self.request)
        return redirect(reverse('dashboard'))

class ContributorsDeadlinesReminder(LoginRequiredMixin, ComradeRequiredMixin, TemplateView):
    template_name = 'home/contributors_deadline_reminder.html'

    def get_context_data(self, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        contributors = get_contributors_with_upcoming_deadlines()

        context = super(ContributorsDeadlinesReminder, self).get_context_data(**kwargs)
        context.update({
            'current_round': current_round,
            'contributors': contributors,
            })
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied("You are not authorized to send reminder emails.")
        current_round = RoundPage.objects.latest('internstarts')
        contributors = get_contributors_with_upcoming_deadlines()

        for c in contributors:
            email.contributor_deadline_reminder(
                    c,
                    current_round,
                    self.request)
        return redirect(reverse('dashboard'))

class ProjectContributions(LoginRequiredMixin, ComradeRequiredMixin, EligibleApplicantRequiredMixin, TemplateView):
    template_name = 'home/project_contributions.html'

    def get_context_data(self, **kwargs):
        current_round = RoundPage.objects.latest('internstarts')

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)
        applicant = get_object_or_404(ApplicantApproval,
                applicant=self.request.user.comrade,
                application_round=current_round,
                approval_status=ApprovalStatus.APPROVED)
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
            'applicant': applicant,
            'contributions': contributions,
            'final_application': final_application,
            })
        return context

# Only submit one contribution at a time
class ContributionUpdate(LoginRequiredMixin, ComradeRequiredMixin, UpdateView):
    fields = [
            'date_started',
            'date_merged',
            'url',
            'description',
            ]

    def get_object(self):
        # Only allow eligible applicants to add contributions
        if not self.request.user.comrade.eligible_application():
            raise PermissionDenied("You are not an eligible applicant or you have not filled out the eligibility check.")

        current_round = RoundPage.objects.latest('internstarts')

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)
        applicant = get_object_or_404(ApplicantApproval,
                applicant=self.request.user.comrade,
                application_round=current_round)
        try:
            application = FinalApplication.objects.get(
                    applicant=applicant,
                    project=project)
        except FinalApplication.DoesNotExist:
            application = None

        if project.has_application_deadline_passed() and application == None:
            raise PermissionDenied("Editing or recording new contributions is closed at this time to applicants who have not created a final application.")

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
        username = kwargs['username']
        current_round = RoundPage.objects.latest('internstarts')
        if current_round.slug != kwargs['round_slug']:
            raise PermissionDenied("You can only rate applicants for the current round.")

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=kwargs['community_slug'],
                project_round__participating_round=current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)
        applicant = get_object_or_404(ApplicantApproval,
                applicant__account__username=username,
                application_round=current_round,
                approval_status=ApprovalStatus.APPROVED)

        # Only allow approved mentors to rank applicants
        approved_mentors = project.get_approved_mentors()
        if request.user.comrade not in [m.mentor for m in approved_mentors]:
            raise PermissionDenied("You are not an approved mentor for this project.")

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
            'spread_the_word',
            ]

    def get_object(self):
        username = self.kwargs.get('username')
        if username:
            comrade = get_object_or_404(Comrade, account__username=username)
        else:
            comrade = self.request.user.comrade

        # Only allow eligible applicants to add contributions
        if not comrade.eligible_application():
            raise PermissionDenied("You are not an eligible applicant or you have not filled out the eligibility check.")

        current_round = RoundPage.objects.latest('internstarts')

        # Make sure both the Community and Project are approved
        project = get_object_or_404(Project,
                slug=self.kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=self.kwargs['community_slug'],
                project_round__participating_round=current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)
        applicant = get_object_or_404(ApplicantApproval,
                applicant=comrade,
                application_round=current_round)
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
        current_round = RoundPage.objects.latest('internstarts')

        # Make sure both the Community, Project, and mentor are approved
        project = get_object_or_404(Project,
                slug=kwargs['project_slug'],
                approval_status=ApprovalStatus.APPROVED,
                project_round__community__slug=kwargs['community_slug'],
                project_round__participating_round=current_round,
                project_round__approval_status=ApprovalStatus.APPROVED)

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
    current_round = RoundPage.objects.latest('internstarts')

    # Make sure both the Community and mentor are approved
    participation = get_object_or_404(Participation,
            community__slug=community_slug,
            participating_round=current_round,
            approval_status=ApprovalStatus.APPROVED)

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
    current_round = RoundPage.objects.latest('internstarts')
    return render(request, 'home/contribution_tips.html', {
        'current_round': current_round,
        })

def eligibility_information(request):
    current_round = RoundPage.objects.latest('internstarts')
    return render(request, 'home/eligibility.html', {
        'current_round': current_round,
        })

class TrustedVolunteersListView(UserPassesTestMixin, ListView):
    template_name = 'home/trusted_volunteers.html'
    queryset = Comrade.objects.filter(
            models.Q(
                mentorapproval__approval_status=ApprovalStatus.APPROVED,
                mentorapproval__project__approval_status=ApprovalStatus.APPROVED,
                mentorapproval__project__project_round__approval_status=ApprovalStatus.APPROVED,
            ) | models.Q(
                coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                coordinatorapproval__community__participation__approval_status=ApprovalStatus.APPROVED,
            )
        ).order_by('public_name').distinct()

    def test_func(self):
        return self.request.user.is_staff

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
class InternSelectionUpdate(LoginRequiredMixin, ComradeRequiredMixin, FormView):
    form_class = InternSelectionForm
    template_name = 'home/internselection_form.html'

    def get_form_kwargs(self):
        kwargs = super(InternSelectionUpdate, self).get_form_kwargs()

        current_round = RoundPage.objects.latest('internstarts')
        this_round = RoundPage.objects.get(slug=self.kwargs['round_slug'])
        if this_round != current_round:
            raise PermissionDenied("You cannot select an intern for a past Outreachy round.")

        set_project_and_applicant(self, current_round)
        application = get_object_or_404(FinalApplication,
                applicant=self.applicant,
                project=self.project)

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
        context['current_round'] = RoundPage.objects.latest('internstarts')
        return context

    def form_valid(self, form):
        form['rating'].save()
        # Fill in the date and IP address of the signed contract
        intern_selection, was_intern_selection_created = InternSelection.objects.get_or_create(
                applicant=self.applicant,
                project=self.project,
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
class InternRemoval(LoginRequiredMixin, ComradeRequiredMixin, DeleteView):
    model = InternSelection
    template_name = 'home/intern_removal_form.html'

    def get_object(self):
        current_round = RoundPage.objects.latest('internstarts')
        this_round = RoundPage.objects.get(slug=self.kwargs['round_slug'])
        if this_round != current_round:
            raise PermissionDenied("You cannot remove an intern from a past Outreachy round.")

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
        context['current_round'] = RoundPage.objects.latest('internstarts')
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

class InternFund(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = RoundPage.objects.latest('internstarts')
        if current_round.slug != kwargs['round_slug']:
            raise PermissionDenied("You can only select funding sources for interns in the current round.")

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

class InternApprove(LoginRequiredMixin, ComradeRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        username = kwargs['applicant_username']
        current_round = RoundPage.objects.latest('internstarts')
        if current_round.slug != kwargs['round_slug']:
            raise PermissionDenied("You can only approve interns in the current round.")

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

@login_required
def dashboard(request):
    """
    Find objects for which the current user is either an approver or a
    submitter, and list them all on one page.
    """
    by_status = defaultdict(list)
    for model in DASHBOARD_MODELS:
        by_model = defaultdict(list)
        for obj in model.objects_for_dashboard(request.user).distinct():
            if obj.approval_status == ApprovalStatus.APPROVED or not has_deadline_passed(obj.submission_and_approval_deadline()):
                by_model[obj.approval_status].append(obj)

        label = model._meta.verbose_name
        for status, objects in by_model.items():
            by_status[status].append((label, objects))

    groups = []
    for status, label in ApprovalStatus.APPROVAL_STATUS_CHOICES:
        group = by_status.get(status)
        if group:
            groups.append((label, group))

    current_round = RoundPage.objects.latest('internstarts')
    pending_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.PENDING).order_by('community__name')
    approved_participations = Participation.objects.filter(
            participating_round = current_round,
            approval_status = ApprovalStatus.APPROVED).order_by('community__name')
    participations = list(chain(pending_participations, approved_participations))

    return render(request, 'home/dashboard.html', {
        'groups': groups,
        'current_round': current_round,
        'pending_participations': pending_participations,
        'approved_participations': approved_participations,
        'participations': participations,
        'show_reminders': 1,
        })
