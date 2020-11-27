import datetime
from django.utils.text import slugify
import factory
import itertools
from wagtail.core.models import Page
from . import models

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: 'user%d' % n)
    password = factory.PostGenerationMethodCall('set_password', 'test')
    email = factory.Faker('email')
    # Outreachy doesn't use the first_name or last_name fields

class ComradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Comrade
        django_get_or_create = ('account',)
        exclude = ('name_suffix',)

    account = factory.SubFactory(UserFactory)

    public_name = factory.Faker('name')

    name_suffix = factory.Faker('suffix')

    @factory.lazy_attribute
    def legal_name(self):
        return "{} {}".format(self.public_name, self.name_suffix)

    pronouns = factory.Iterator(models.Comrade.PRONOUN_CHOICES, getter=lambda c: c[0])

    @factory.lazy_attribute
    def agreed_to_code_of_conduct(self):
        return self.legal_name


class CoordinatorFactory(ComradeFactory):
    "Subclass of ComradeFactory with specialized usernames for coordinators."
    account__username = factory.Iterator(
        ('coordinator{}'.format(n) for n in itertools.count(1)),
        cycle=False,
    )


class ReviewerFactory(ComradeFactory):
    "Subclass of ComradeFactory with specialized usernames for application reviewers."
    account__username = factory.Iterator(
        ('reviewer{}'.format(n) for n in itertools.count(1)),
        cycle=False,
    )


class MentorFactory(ComradeFactory):
    "Subclass of ComradeFactory with specialized usernames for project mentors."
    account__username = factory.Iterator(
        ('mentor{}'.format(n) for n in itertools.count(1)),
        cycle=False,
    )


class ApplicantFactory(ComradeFactory):
    "Subclass of ComradeFactory with specialized usernames for applicants."
    account__username = factory.Iterator(
        ('applicant{}'.format(n) for n in itertools.count(1)),
        cycle=False,
    )


class PageFactory(factory.Factory):
    """
    Base factory for constructing Wagtail pages. By default the page will be
    placed immediately under the existing home page, but you can make it a
    child of another page instead by setting ``child_of``.
    """

    class Meta:
        abstract = True

    title = factory.Faker('sentence', nb_words=3)
    slug = factory.Faker('slug')
    child_of = None

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        kwargs.pop('child_of', None)
        return model_class(*args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        parent = kwargs.pop('child_of') or Page.objects.get(sites_rooted_here__isnull=False)
        obj = model_class(*args, **kwargs)
        return parent.add_child(instance=obj)

round_dates = (
    'pingold',
    'orgreminder',
    'initial_applications_open',
    'lateorgs',
    'outreachy_chat',
    'initial_applications_close',
    'landingdue',
    'lateprojects',
    'contributions_open',
    'contributions_close',
    'mentor_intern_selection_deadline',
    'coordinator_funding_deadline',
    'internapproval',
    'internannounce',
    'internstarts',
    'week_two_chat_text_date',
    'tax_form_deadline',
    'initialfeedback',
    'week_four_chat_text_date',
    'week_six_chat_text_date',
    'week_eight_chat_text_date',
    'initial_payment_date',
    'midfeedback',
    'week_ten_chat_text_date',
    'week_twelve_chat_text_date',
    'midpoint_payment_date',
    'week_fourteen_chat_text_date',
    'internends',
    'finalfeedback',
    'final_payment_date',
)

class RoundPageFactory(PageFactory):
    """
    Constructs a RoundPage that has a roughly-reasonable timeline. By default,
    ``pingnew`` is set to today and all the later deadlines are set from there.

    But you can override which deadline you build the timeline from by setting,
    for example, ``start_from="internstarts"``. If you want that deadline to
    occur some number of days after today, set ``days_after_today``; set it to
    a negative number to make it occur before today instead.

    Finally, you can change the delay between adjacent deadlines: for example,
    if you want a shorter delay between ``orgreminder`` and ``landingdue``, you
    could set ``landingdue=datetime.timedelta(days=7)``.

    If you change the order of any of the round date fields in this function,
    you must change the ordering in the list above.
    """

    class Meta:
        model = models.RoundPage

    class Params:
        start_from = 'pingnew'
        days_after_today = 0
        chat_text_time = datetime.time(13, 0, tzinfo=datetime.timezone.utc)

    roundnumber = factory.Sequence(int)

    # week 0 - Jan 8 / Aug 6
    pingold = datetime.timedelta(days=0)
    # week 1
    orgreminder = datetime.timedelta(days=7)
    # week 2 - Jan 22 / Aug 20
    initial_applications_open = datetime.timedelta(days=7)
    # week 3
    # week 4 - Feb 5 / Sept 3
    lateorgs = datetime.timedelta(days=14)
    # week 5 - Monday Feb 12 / Sept 9
    outreachy_chat = datetime.timedelta(days=7)
    # week 6
    # week 7 - Feb 26 / Sept 24 - "soft" deadline for project submission
    # week 7 - Feb 26 / Sept 24 - deadline for submitting initial applications
    initial_applications_close = datetime.timedelta(days=14)
    landingdue = datetime.timedelta(days=0)
    # week 8 - Mar 5 / Oct 1 - deadline for approving initial apps & projects
    lateprojects = datetime.timedelta(days=7)
    contributions_open = datetime.timedelta(days=0)
    # week 9
    # week 10
    # week 11
    # week 12
    # week 13 - Apr 9 / Nov 5 - contribution and final application deadline
    contributions_close = datetime.timedelta(days=35)
    # week 14
    # week 15 - Apr 18 / Nov 14 - deadline for intern selection
    mentor_intern_selection_deadline = datetime.timedelta(days=9)
    # week 16 - Apr 22 / Nov 18 - deadline for coordinators to set intern funding
    coordinator_funding_deadline = datetime.timedelta(days=4)
    # week 16 - Apr 23 / Nov 19 - thanksgiving holiday
    internapproval = datetime.timedelta(days=1)
    # For the December round, there's a short delay between the intern announcement
    # and when the interns start.
    #
    # week 17 - Nov 26
    # week 18 - Dec 3 - interns start
    #
    # Pass the following parameters to set up the December round:
    # internapproval = datetime.timedelta(days=1),
    # internannounce = datetime.timedelta(days=7),
    # internstarts=datetime.timedelta(days=7),
    #
    #
    # The May round aligns with Google summer of Code, so there's a longer
    # period between when interns are announced and when they start
    # in the Outreachy May round. The code below sets up the May round:
    # week 17
    # week 18
    internannounce = datetime.timedelta(days=14)
    # week 20 - May 20
    internstarts = datetime.timedelta(days=14)
    week_two_chat_text_date = datetime.timedelta(days=7)
    tax_form_deadline = datetime.timedelta(days=5)
    initialfeedback = datetime.timedelta(days=3)
    week_four_chat_text_date = datetime.timedelta(days=6)
    week_six_chat_text_date = datetime.timedelta(days=14)
    week_eight_chat_text_date = datetime.timedelta(days=14)
    initial_payment_date = datetime.timedelta(days=1)
    midfeedback = datetime.timedelta(days=7)
    week_ten_chat_text_date = datetime.timedelta(days=6)
    week_twelve_chat_text_date = datetime.timedelta(days=14)
    midpoint_payment_date = datetime.timedelta(days=9)
    week_fourteen_chat_text_date = datetime.timedelta(days=5)
    internends = datetime.timedelta(days=0)
    finalfeedback = datetime.timedelta(days=7)
    final_payment_date = datetime.timedelta(days=30)

    @factory.lazy_attribute
    def pingnew(obj):
        """
        If the specified start date is relative to the middle of the round,
        walk it back through all the specified timedeltas to find the date of
        the event which is supposed to be earliest in the round.
        """
        start = models.get_deadline_date_for(
            datetime.datetime.now(datetime.timezone.utc)
        )
        start += datetime.timedelta(days=obj.days_after_today)

        if obj.start_from != 'pingnew':
            assert obj.start_from in round_dates, "unknown RoundPage field: " + repr(obj.start_from)
            for field_name in round_dates:
                start -= getattr(obj, field_name)
                if obj.start_from == field_name:
                    break
        return start

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        """
        Turn all the timedeltas into concrete dates by walking forward from
        ``pingnew``.
        """
        previous = kwargs['pingnew']
        for field_name in round_dates:
            previous += kwargs[field_name]
            if field_name.endswith('_chat_text_date'):
                kwargs[field_name] = datetime.datetime.combine(previous, kwargs['chat_text_time'])
            elif field_name == 'outreachy_chat':
                chat_time = datetime.time(16, 0, tzinfo=datetime.timezone.utc)
                kwargs[field_name] = datetime.datetime.combine(previous, chat_time)
            else:
                kwargs[field_name] = previous
        kwargs['title'] = kwargs['internstarts'].strftime('Outreachy %B %Y internship round')
        kwargs['slug'] = slugify(kwargs['title'])
        return kwargs

class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Community

    name = factory.Faker('word')
    slug = factory.Faker('slug')
    description = factory.Faker('paragraph')

class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Notification
        django_get_or_create = ('community', 'comrade')

    community = factory.SubFactory(CommunityFactory)
    comrade = factory.SubFactory(ComradeFactory)

class ParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Participation

    community = factory.SubFactory(CommunityFactory)
    participating_round = factory.SubFactory(RoundPageFactory)

class SponsorshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Sponsorship

    participation = factory.SubFactory(ParticipationFactory)
    coordinator_can_update = True
    name = factory.Faker('name')
    amount = 6500
    funding_decision_date = datetime.date.today()

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project
        django_get_or_create = ('slug', 'project_round')

    project_round = factory.SubFactory(ParticipationFactory)
    short_title = factory.Faker('sentence')
    slug = factory.Faker('slug')

    contribution_tasks = factory.Faker('paragraph')

class MentorApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MentorApproval
        django_get_or_create = ('mentor', 'project')

    mentor = factory.SubFactory(ComradeFactory)
    project = factory.SubFactory(ProjectFactory)

    mentor_foss_contributions = factory.Faker('paragraph')
    mentorship_style = factory.Faker('paragraph')
    employer = factory.Faker('name')

class CoordinatorApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CoordinatorApproval
        django_get_or_create = ('coordinator', 'community')

    coordinator = factory.SubFactory(ComradeFactory)
    community = factory.SubFactory(CommunityFactory)

class ApplicationReviewerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ApplicationReviewer
        django_get_or_create = ('comrade', 'reviewing_round')

    comrade = factory.SubFactory(ComradeFactory)
    reviewing_round = factory.SubFactory(RoundPageFactory)

class ApplicantApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ApplicantApproval
        django_get_or_create = ('applicant', 'application_round')

    applicant = factory.SubFactory(ComradeFactory)
    application_round = factory.SubFactory(RoundPageFactory)
    submission_date = factory.Faker('past_date')
    ip_address = factory.Faker('ipv4_public')

class ContributionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Contribution
        django_get_or_create = ('applicant', 'project')

    class Params:
        round = factory.SubFactory(RoundPageFactory, start_from='contributions_close')

    applicant = factory.SubFactory(
        ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        approval_status=models.ApprovalStatus.APPROVED,
    )
    project = factory.SubFactory(
        ProjectFactory,
        project_round__participating_round=factory.SelfAttribute('...round'),
        approval_status=models.ApprovalStatus.APPROVED,
        project_round__approval_status=models.ApprovalStatus.APPROVED,
    )

    date_started = factory.Faker('past_date')
    url = factory.Faker('url')
    description = factory.Faker('paragraph')

class FinalApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FinalApplication
        django_get_or_create = ('applicant', 'project')

    class Params:
        round = factory.SubFactory(RoundPageFactory, start_from='internannounce')

    applicant = factory.SubFactory(
        ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        approval_status=models.ApprovalStatus.APPROVED,
    )
    project = factory.SubFactory(
        ProjectFactory,
        project_round__participating_round=factory.SelfAttribute('...round'),
        approval_status=models.ApprovalStatus.APPROVED,
        project_round__approval_status=models.ApprovalStatus.APPROVED,
    )

    experience = factory.Faker('paragraph')
    foss_experience = factory.Faker('paragraph')
    relevant_projects = factory.Faker('paragraph')
    time_correct = True

    spread_the_word = factory.Iterator(models.FinalApplication.HEARD_CHOICES, getter=lambda c: c[0])

    @factory.post_generation
    def contributions(self, create, extracted, **kwargs):
        # create a contribution unless contributions=0 is explicitly specified
        if extracted is None:
            extracted = 1

        if not create:
            return

        # allow contributions=3 to generate 3 new contributions
        for _ in range(extracted):
            ContributionFactory.create(
                applicant=self.applicant,
                project=self.project,
                round=self.applicant.application_round,
            )

class SignedContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SignedContract

    text = factory.Faker('text')
    legal_name = factory.Faker('name')
    ip_address = factory.Faker('ipv4_public')
    date_signed = factory.Faker('past_date')

class InternSelectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.InternSelection
        django_get_or_create = ('applicant', 'project')

    class Params:
        round = factory.SubFactory(RoundPageFactory, start_from='internannounce')

        signed = factory.Trait(
            intern_contract=factory.SubFactory(SignedContractFactory)
        )

        active = factory.Trait(
            # checked by home.views.intern_in_good_standing()
            organizer_approved=True,
            in_good_standing=True,

            # but these also ought to be set
            signed=True,
            funding_source=models.InternSelection.ORG_FUNDED,
            # mentors=1, # the post_generation function is not called if this is set
        )

    # set all the approval_status fields to APPROVED, because an
    # InternSelection object can only be created if
    # home.views.set_project_and_applicant succeeds

    applicant = factory.SubFactory(
        ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        approval_status=models.ApprovalStatus.APPROVED,
    )
    project = factory.SubFactory(
        ProjectFactory,
        project_round__participating_round=factory.SelfAttribute('...round'),
        approval_status=models.ApprovalStatus.APPROVED,
        project_round__approval_status=models.ApprovalStatus.APPROVED,
    )

    intern_starts = factory.SelfAttribute('round.internstarts')
    initial_feedback_due = factory.SelfAttribute('round.initialfeedback')
    initial_feedback_opens = factory.LazyAttribute(lambda o: o.initial_feedback_due - datetime.timedelta(days=7))
    midpoint_feedback_due = factory.SelfAttribute('round.midfeedback')
    midpoint_feedback_opens = factory.LazyAttribute(lambda o: o.midpoint_feedback_due - datetime.timedelta(days=7))
    final_feedback_due = factory.SelfAttribute('round.finalfeedback')
    final_feedback_opens = factory.LazyAttribute(lambda o: o.final_feedback_due - datetime.timedelta(days=7))
    intern_ends = factory.SelfAttribute('round.internends')

    @factory.post_generation
    def mentors(self, create, extracted, **kwargs):
        # create a mentor unless mentors=0 is explicitly specified
        if extracted is None:
            extracted = 1

        if not create:
            return

        defaults = {
            'mentor__approval_status': models.ApprovalStatus.APPROVED,
        }
        defaults.update(kwargs)

        # allow mentors=3 to generate 3 new mentors
        for _ in range(extracted):
            MentorRelationshipFactory.create(
                intern_selection=self,
                mentor__project=self.project,
                **defaults
            )

    @factory.post_generation
    def finalapplication(self, create, extracted, **kwargs):
        # ignore finalapplication=0 because we always want to create one final application
        if not create or extracted:
            return

        FinalApplicationFactory.create(
            applicant=self.applicant,
            project=self.project,
            round=self.applicant.application_round,
        )

class MentorRelationshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MentorRelationship
        django_get_or_create = ('intern_selection', 'mentor')

    intern_selection = factory.SubFactory(InternSelectionFactory)
    mentor = factory.SubFactory(MentorApprovalFactory)
    contract = factory.SubFactory(SignedContractFactory)

class InitialMentorFeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.InitialMentorFeedback
        django_get_or_create = ('intern_selection',)

    intern_selection = factory.SubFactory(
        InternSelectionFactory,
        active=True,
        round__start_from='initialfeedback',
    )
    allow_edits = False
    ip_address = factory.Faker('ipv4_public')

    in_contact = True
    asking_questions = True
    active_in_public = True
    provided_onboarding = True

    checkin_frequency = factory.Iterator(models.InitialMentorFeedback.CHECKIN_FREQUENCY_CHOICES, getter=lambda c: c[0])

    last_contact = factory.Faker('past_date')

    intern_response_time = factory.Iterator(models.InitialMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])
    mentor_response_time = factory.Iterator(models.InitialMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])

    progress_report = factory.Faker('paragraph')

    full_time_effort = True

    payment_approved = True

    request_extension = False

    request_termination = False

class MidpointMentorFeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MidpointMentorFeedback
        django_get_or_create = ('intern_selection',)

    intern_selection = factory.SubFactory(
        InternSelectionFactory,
        active=True,
        round__start_from='midfeedback',
    )
    allow_edits = False
    ip_address = factory.Faker('ipv4_public')

    intern_help_requests_frequency = factory.Iterator(models.MidpointMentorFeedback.ASKING_FOR_HELP_FREQUENCY_CHOICES, getter=lambda c: c[0])
    mentor_help_response_time = factory.Iterator(models.MidpointMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])
    intern_contribution_frequency = factory.Iterator(models.MidpointMentorFeedback.CONTRIBUTION_FREQUENCY_CHOICES, getter=lambda c: c[0])
    mentor_review_response_time = factory.Iterator(models.MidpointMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])
    intern_contribution_revision_time = factory.Iterator(models.MidpointMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])

    last_contact = factory.Faker('past_date')

    progress_report = factory.Faker('paragraph')

    full_time_effort = True

    payment_approved = True

    request_extension = False

    request_termination = False

class FinalMentorFeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FinalMentorFeedback
        django_get_or_create = ('intern_selection',)

    intern_selection = factory.SubFactory(
        InternSelectionFactory,
        active=True,
        round__start_from='midfeedback',
    )
    allow_edits = False
    ip_address = factory.Faker('ipv4_public')

    intern_help_requests_frequency = factory.Iterator(models.FinalMentorFeedback.ASKING_FOR_HELP_FREQUENCY_CHOICES, getter=lambda c: c[0])
    mentor_help_response_time = factory.Iterator(models.FinalMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])
    intern_contribution_frequency = factory.Iterator(models.FinalMentorFeedback.CONTRIBUTION_FREQUENCY_CHOICES, getter=lambda c: c[0])
    mentor_review_response_time = factory.Iterator(models.FinalMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])
    intern_contribution_revision_time = factory.Iterator(models.FinalMentorFeedback.RESPONSE_TIME_CHOICES, getter=lambda c: c[0])

    last_contact = factory.Faker('past_date')

    progress_report = factory.Faker('paragraph')

    full_time_effort = True

    payment_approved = True

    request_extension = False

    request_termination = False

    mentoring_recommended = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    blog_frequency = factory.Iterator(models.FinalMentorFeedback.BLOG_FREQUENCY, getter=lambda c: c[0])
    blog_prompts_caused_writing = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    blog_prompts_caused_overhead = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    recommend_blog_prompts = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    zulip_caused_intern_discussion = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    zulip_caused_mentor_discussion = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])
    recommend_zulip = factory.Iterator(models.FinalMentorFeedback.SURVEY_RESPONSES, getter=lambda c: c[0])

    feedback_for_organizers = factory.Faker('paragraph')
