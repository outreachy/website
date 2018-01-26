from collections import defaultdict
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import inlineformset_factory, modelform_factory, widgets
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from formtools.wizard.views import SessionWizardView
from registration.backends.hmac import views as hmac_views

from . import email

from .mixins import ApprovalStatusAction
from .mixins import ComradeRequiredMixin
from .mixins import Preview

from .models import ApplicantApproval
from .models import ApprovalStatus
from .models import CommunicationChannel
from .models import Community
from .models import Comrade
from .models import CoordinatorApproval
from .models import DASHBOARD_MODELS
from .models import MentorApproval
from .models import NewCommunity
from .models import Notification
from .models import Participation
from .models import Project
from .models import ProjectSkill
from .models import RoundPage
from .models import SchoolInformation
from .models import Sponsorship

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
            ]

    # FIXME - we need to migrate any existing staff users who aren't a Comrade
    # to the Comrade model instead of the User model.
    def get_object(self):
        # Either grab the current comrade to update, or make a new one
        try:
            return self.request.user.comrade
        except Comrade.DoesNotExist:
            return Comrade(
                    account=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ComradeUpdate, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '/')
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
    # Collect the rest of the information on the forms
    # FIXME: then ask them to contact the organizers
    if cleaned_data['us_sanctioned_country']:
        return True
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
    return cleaned_data.get('contractor', True) or cleaned_data.get('employed', True)

def show_time_commitment_info(wizard):
    if not gender_and_demographics_is_approved(wizard):
        return False
    cleaned_data = wizard.get_cleaned_data_for_step('Time Commitments') or {}
    return cleaned_data.get('time_commitments', True)

class EligibilityUpdateView(LoginRequiredMixin, SessionWizardView):
    template_name = 'home/wizard_form.html'
    condition_dict = {
            'USA demographics': show_us_demographics,
            'Gender Identity': general_info_is_approved,
            'Time Commitments': gender_and_demographics_is_approved,
            'School Info': show_school_info,
            'School Term Info': show_school_info,
            'Contractor Info': show_contractor_info,
            'Employment Info': show_employment_info,
            'Time Commitment Info': show_time_commitment_info,
            }
    form_list = [
            ('General Info', modelform_factory(ApplicantApproval, fields=(
                'over_18',
                'gsoc_or_outreachy_internship',
                'eligible_to_work',
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
                    'transgender': widgets.CheckboxInput(),
                    'genderqueer': widgets.CheckboxInput(),
                    'man': widgets.CheckboxInput(),
                    'woman': widgets.CheckboxInput(),
                    'demi_boy': widgets.CheckboxInput(),
                    'demi_girl': widgets.CheckboxInput(),
                    'non_binary': widgets.CheckboxInput(),
                    'demi_non_binary': widgets.CheckboxInput(),
                    'genderqueer': widgets.CheckboxInput(),
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
                'employed',
                'contractor',
                'time_commitments',
                ),
                widgets = {
                    'enrolled_as_student': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'employed': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'contractor': widgets.RadioSelect(choices=BOOL_CHOICES),
                    'time_commitments': widgets.RadioSelect(choices=BOOL_CHOICES),
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
                extra=3,
                can_delete=False,
                fields=(
                    'term_number',
                    'term_name',
                    'start_date',
                    'end_date',
                    'typical_credits',
                    'registered_credits',
                    'outreachy_credits',
                    'thesis_credits',
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
                ))),
            ('Employment Info', inlineformset_factory(ApplicantApproval,
                EmploymentTimeCommitment,
                min_num=1,
                validate_min=True,
                extra=3,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                ))),
            ('Time Commitment Info', inlineformset_factory(ApplicantApproval,
                TimeCommitment,
                min_num=1,
                validate_min=True,
                extra=3,
                can_delete=False,
                fields=(
                    'start_date',
                    'end_date',
                    'hours_per_week',
                ))),
            ]

    def get_form_instance(self, step):
        # This implementation ignores `step` which is fine as long as
        # all of the forms are supposed to edit the same base object and
        # are either ModelForm or InlineModelForm.

        # Make sure to use the same Python object for all steps, rather
        # than constructing a different empty object for each step, by
        # caching it on this view instance.
        if not getattr(self, 'object', None):
            try:
                current_round = RoundPage.objects.latest('internstarts')
                self.object = ApplicantApproval.objects.get(
                        applicant=self.request.user.comrade,
                        application_round=current_round)
            except ApplicantApproval.DoesNotExist:
                self.object = ApplicantApproval(
                        application_round=RoundPage.objects.latest('internstarts'),
                        applicant=self.request.user.comrade)
        return self.object

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

        # Make sure to commit the object to the database before saving
        # any of the InlineFormSets, so they can set their foreign keys
        # to point to this object.
        self.object.save()

        for inlineformset in inlines:
            inlineformset.save()

        self.object.approval_status = ApprovalStatus.REJECTED
        # Do they meet our general requirements,
        # demographics requirements, and time requirements?
        if general_info_is_approved(self) and gender_and_demographics_is_approved(self) and self.time_commitments_are_approved():
            self.object.approval_status = ApprovalStatus.APPROVED
            if self.object.us_sanctioned_country or self.object.prefer_not_to_say or self.object.self_identify != '':
                self.object.approval_status = ApprovalStatus.PENDING

        # Make sure to save the application status
        # We have to do this twice because we have to save the inlines
        # before searching for them in the database (which the call to is_eligible will do)
        self.object.save()

        # FIXME: This should redirect somewhere appropriate.
        return redirect('/')

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
            notification = Notification.objects.get(comrade=request.user.comrade, community=community)
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
    approved_projects = [p for p in projects if p.accepting_new_applicants]
    closed_projects = [p for p in projects if not p.accepting_new_applicants]

    return render(request, 'home/community_landing.html',
            {
            'participation_info': participation_info,
            'approved_projects': approved_projects,
            'closed_projects': closed_projects,
            # TODO: make the template get these off the participation_info instead of passing them in the context
            'current_round' : participation_info.participating_round,
            'community': participation_info.community,
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
    fields = ['name', 'description', 'long_description', 'website']

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
    required_skills = project.projectskill_set.filter(required=ProjectSkill.STRONG)
    preferred_skills = project.projectskill_set.filter(required=ProjectSkill.OPTIONAL)
    bonus_skills = project.projectskill_set.filter(required=ProjectSkill.BONUS)

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
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'bonus_skills': bonus_skills,
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
            approval = MentorApproval.objects.get(mentor=mentor, project=project)
        except MentorApproval.DoesNotExist:
            approval = MentorApproval(mentor=mentor, project=project)

        # Capture the old instructions_read before saving the form.
        self.instructions_already_read = approval.instructions_read
        return approval

    def get_success_url(self):
        if not self.instructions_already_read and self.object.project.is_submitter(self.request.user):
            # This is the first time this mentor has submitted this
            # form, but they're already approved, so we must be in the
            # middle of the "propose a new project" workflow.
            return reverse('project-skills-edit', kwargs={
                'community_slug': self.object.project.project_round.community.slug,
                'project_slug': self.object.project.slug,
                })

        return self.object.get_preview_url()

    def notify(self):
        if self.prior_status != self.target_status:
            email.approval_status_changed(self.object, self.request)

class ProjectAction(ApprovalStatusAction):
    fields = ['short_title', 'approved_license', 'unapproved_license_description', 'no_proprietary_software', 'proprietary_software_description', 'longevity', 'community_size', 'community_benefits', 'intern_tasks', 'intern_benefits', 'repository', 'issue_tracker', 'newcomer_issue_tag', 'long_description', 'accepting_new_applicants']

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
            raise PermissionDenied("You are not an approved mentor for this project.")
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

@login_required
def dashboard(request):
    """
    Find objects for which the current user is either an approver or a
    submitter, and list them all on one page.
    """
    by_status = defaultdict(list)
    for model in DASHBOARD_MODELS:
        objects = model.objects_for_dashboard(request.user).distinct()
        for obj in objects:
            by_status[obj.approval_status].append((model._meta.verbose_name, obj))

    groups = []
    for status, label in ApprovalStatus.APPROVAL_STATUS_CHOICES:
        group = by_status.get(status)
        if group:
            groups.append((label, group))

    return render(request, 'home/dashboard.html', {
        'groups': groups,
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
