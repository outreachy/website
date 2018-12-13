import datetime
import factory
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
    nick_name = factory.Faker('first_name')

    name_suffix = factory.Faker('suffix')

    @factory.lazy_attribute
    def legal_name(self):
        return "{} {}".format(self.public_name, self.name_suffix)

    pronouns = factory.Iterator(models.Comrade.PRONOUN_CHOICES, getter=lambda c: c[0])

    @factory.lazy_attribute
    def agreed_to_code_of_conduct(self):
        return self.legal_name

class PageFactory(factory.Factory):
    """
    Base factory for constructing Wagtail pages. By default the page will be a
    new root page, but you can make it a child of an existing page instead by
    setting ``child_of``.
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
        child_of = kwargs.pop('child_of')
        obj = model_class(*args, **kwargs)
        if child_of:
            return child_of.add_child(instance=obj)
        else:
            return model_class.add_root(instance=obj)

round_dates = (
    'pingold',
    'orgreminder',
    'landingdue',
    'appsopen',
    'lateorgs',
    'lateprojects',
    'appsclose',
    'appslate',
    'mentor_intern_selection_deadline',
    'coordinator_funding_deadline',
    'internapproval',
    'internannounce',
    'internstarts',
    'initialfeedback',
    'midfeedback',
    'internends',
    'finalfeedback',
)

class RoundPageFactory(PageFactory):
    """
    Constructs a RoundPage that has a roughly-reasonable timeline. By default,
    ``pingnew`` is set to today and all the later deadlines are set from there.

    But you can override which deadline you build the timeline from by setting,
    for example, ``start_from="internstarts"``; and you can set the date for
    that deadline with ``start_date``.

    Finally, you can change the delay between adjacent deadlines: for example,
    if you want a shorter delay between ``orgreminder`` and ``landingdue``, you
    could set ``landingdue=datetime.timedelta(days=7)``.
    """

    class Meta:
        model = models.RoundPage

    class Params:
        start_from = 'pingnew'
        start_date = factory.LazyFunction(datetime.date.today)

    roundnumber = factory.Sequence(int)

    pingold = datetime.timedelta(days=6)
    orgreminder = datetime.timedelta(days=7)
    landingdue = datetime.timedelta(days=14)
    appsopen = datetime.timedelta(days=10)
    lateorgs = datetime.timedelta(days=25)
    lateprojects = datetime.timedelta(days=14)
    appsclose = datetime.timedelta(days=7)
    appslate = datetime.timedelta(days=7)
    mentor_intern_selection_deadline = datetime.timedelta(days=3)
    coordinator_funding_deadline = datetime.timedelta(days=1)
    internapproval = datetime.timedelta(days=2)
    internannounce = datetime.timedelta(days=4)
    internstarts = datetime.timedelta(days=26)
    initialfeedback = datetime.timedelta(days=15)
    midfeedback = datetime.timedelta(days=42)
    internends = datetime.timedelta(days=33)
    finalfeedback = datetime.timedelta(days=7)

    @factory.lazy_attribute
    def pingnew(obj):
        """
        If the specified start date is relative to the middle of the round,
        walk it back through all the specified timedeltas to find the date of
        the event which is supposed to be earliest in the round.
        """
        start = obj.start_date
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
            kwargs[field_name] = previous
        return kwargs

class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Community

    name = factory.Faker('word')
    slug = factory.Faker('slug')
    description = factory.Faker('paragraph')

class ParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Participation

    community = factory.SubFactory(CommunityFactory)
    participating_round = factory.SubFactory(RoundPageFactory)

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project
        django_get_or_create = ('slug', 'project_round')

    project_round = factory.SubFactory(ParticipationFactory)
    short_title = factory.Faker('sentence')
    slug = factory.Faker('slug')

    contribution_tasks = factory.Faker('paragraph')
    deadline = models.Project.ONTIME

class MentorApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MentorApproval
        django_get_or_create = ('mentor', 'project')

    mentor = factory.SubFactory(ComradeFactory)
    project = factory.SubFactory(ProjectFactory)

    mentor_foss_contributions = factory.Faker('paragraph')
    mentorship_style = factory.Faker('paragraph')

class ApplicantApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ApplicantApproval
        django_get_or_create = ('applicant', 'application_round')

    applicant = factory.SubFactory(ComradeFactory)
    application_round = factory.SubFactory(RoundPageFactory)
    submission_date = factory.Faker('past_date')
    ip_address = factory.Faker('ipv4_public')

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
            project__approval_status=models.ApprovalStatus.APPROVED,
            project__project_round__approval_status=models.ApprovalStatus.APPROVED,
            organizer_approved=True,
            in_good_standing=True,

            # but these also ought to be set
            signed=True,
            #mentors=1, # the post_generation function is not called if this is set
        )

    applicant = factory.SubFactory(ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
    )
    project = factory.SubFactory(ProjectFactory,
        project_round__participating_round=factory.SelfAttribute('...round'),
    )

    @factory.post_generation
    def mentors(self, create, extracted, **kwargs):
        # create a mentor unless mentors=0 is explicitly specified
        if extracted is None:
            extracted = 1

        if not create:
            return

        # allow mentors=3 to generate 3 new mentors
        for _ in range(extracted):
            MentorRelationshipFactory.create(
                intern_selection=self,
                mentor__project=self.project,
                **kwargs
            )

class MentorRelationshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MentorRelationship
        django_get_or_create = ('intern_selection', 'mentor')

    intern_selection = factory.SubFactory(InternSelectionFactory)
    mentor = factory.SubFactory(MentorApprovalFactory)
    contract = factory.SubFactory(SignedContractFactory)
