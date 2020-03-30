"""
Meta-factories which combine the individual factories from factories.py to set
up complete scenarios which are useful for various testing purposes.
"""

import datetime
import factory
from . import factories
from home.models import ApprovalStatus
from home.models import InternSelection

class Scenario(object):
    def __init__(self, **kwargs):
        # Just assign all keyword arguments to fields of the same name. So
        # after `s = Scenario(username='coordinator1')`, `s.username` returns
        # 'coordinator1'. This way the fields in the following factories define
        # exactly what fields are returned.
        self.__dict__.update(kwargs)


class NewRoundScenario(factory.Factory):
    """
    Create samples of the objects which matter when an Outreachy organizer is
    preparing for a new internship round. This includes communities and
    coordinators from past rounds, but does not include any participation
    objects for the new round yet.
    """

    class Meta:
        model = Scenario

    coordinator = factory.SubFactory(factories.CoordinatorFactory)

    community = factory.SubFactory(factories.CommunityFactory)

    coordinator_approval = factory.SubFactory(
        factories.CoordinatorApprovalFactory,
        coordinator=factory.SelfAttribute('..coordinator'),
        community=factory.SelfAttribute('..community'),
        approval_status=ApprovalStatus.APPROVED,
    )

    reviewer = factory.SubFactory(factories.ReviewerFactory)

    round = factory.SubFactory(factories.RoundPageFactory)

    reviewer_approval = factory.SubFactory(
        factories.ApplicationReviewerFactory,
        comrade=factory.SelfAttribute('..reviewer'),
        reviewing_round=factory.SelfAttribute('..round'),
        approval_status=ApprovalStatus.APPROVED,
    )


class CommunitySignupUnderwayScenario(NewRoundScenario):
    """
    Create samples of the objects in the middle of the period
    where communities are signing up, but before initial applications opens.
    """

    round__start_from = 'pingold'

    mentor = factory.SubFactory(factories.MentorFactory)

    participation = factory.SubFactory(
        factories.ParticipationFactory,
        community=factory.SelfAttribute('..community'),
        participating_round=factory.SelfAttribute('..round'),
        approval_status=ApprovalStatus.APPROVED,
    )

    sponsorship = factory.SubFactory(
        factories.SponsorshipFactory,
        participation=factory.SelfAttribute('..participation'),
    )

    project = factory.SubFactory(
        factories.ProjectFactory,
        project_round=factory.SelfAttribute('..participation'),
        approval_status=ApprovalStatus.APPROVED,
    )

    mentor_approval = factory.SubFactory(
        factories.MentorApprovalFactory,
        mentor=factory.SelfAttribute('..mentor'),
        project=factory.SelfAttribute('..project'),
        approval_status=ApprovalStatus.APPROVED,
    )

class InitialApplicationsUnderwayScenario(CommunitySignupUnderwayScenario):
    """
    Create samples of the objects in the middle of the initial application period.
    """
    round__start_from = 'initial_applications_open'

    applicant1 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        applicant=factory.SubFactory(factories.ApplicantFactory),
        application_round=factory.SelfAttribute('..round'),
        approval_status=ApprovalStatus.APPROVED,
    )
    applicant2 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.APPROVED,
    )
    applicant3 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.APPROVED,
    )
    applicant4 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.PENDING,
    )
    applicant5 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.REJECTED,
        reason_denied='TIME',
    )
    applicant6 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.REJECTED,
        reason_denied='ALIGNMENT',
    )
    applicant7 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.REJECTED,
        reason_denied='GENERAL',
    )
    applicant8 = factory.SubFactory(
        factories.ApplicantApprovalFactory,
        application_round=factory.SelfAttribute('..round'),
        applicant=factory.SubFactory(factories.ApplicantFactory),
        approval_status=ApprovalStatus.APPROVED,
    )

class ContributionsUnderwayScenario(InitialApplicationsUnderwayScenario):
    """
    Create samples of the objects in the middle of the contribution period.
    """
    round__start_from = 'contributions_open'
    sponsorship__amount = 13000

    mentor2 = factory.SubFactory(factories.MentorFactory)
    mentor3 = factory.SubFactory(factories.MentorFactory)

    project2 = factory.SubFactory(
        factories.ProjectFactory,
        project_round=factory.SelfAttribute('..participation'),
        approval_status=ApprovalStatus.APPROVED,
    )
    project3 = factory.SubFactory(
        factories.ProjectFactory,
        project_round=factory.SelfAttribute('..participation'),
        approval_status=ApprovalStatus.APPROVED,
    )

    mentor_approval2 = factory.SubFactory(
        factories.MentorApprovalFactory,
        mentor=factory.SelfAttribute('..mentor2'),
        project=factory.SelfAttribute('..project2'),
        approval_status=ApprovalStatus.APPROVED,
    )
    mentor_approval3 = factory.SubFactory(
        factories.MentorApprovalFactory,
        mentor=factory.SelfAttribute('..mentor3'),
        project=factory.SelfAttribute('..project3'),
        approval_status=ApprovalStatus.APPROVED,
    )

    # Create final applications.
    # This will automatically create 1 recorded contribution per application.
    final_application1 = factory.SubFactory(
        factories.FinalApplicationFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant1'),
        approval_status=ApprovalStatus.APPROVED,
        project=factory.SelfAttribute('..project'),
        time_correct=True,
    )
    contribution_applicant2 = factory.SubFactory(
        factories.ContributionFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant1'),
        project=factory.SelfAttribute('..project2'),
    )

class ContributionsClosedScenario(ContributionsUnderwayScenario):
    """
    Create samples of the objects which matter before mentors start to
    select the interns they want to work with.
    """

    round__start_from = 'contributions_close'

    # Create final applications.
    # This will automatically create 1 recorded contribution per application.
    final_application2 = factory.SubFactory(
        factories.FinalApplicationFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant2'),
        approval_status=ApprovalStatus.APPROVED,
        project=factory.SelfAttribute('..project2'),
        time_correct=False,
    )
    final_application3 = factory.SubFactory(
        factories.FinalApplicationFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant3'),
        project=factory.SelfAttribute('..project3'),
        approval_status=ApprovalStatus.APPROVED,
        time_correct=True,
        time_updates="I didn't list my job on the initial application, but I am sure I can take a leave of absence.",
    )
    final_application8 = factory.SubFactory(
        factories.FinalApplicationFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant8'),
        project=factory.SelfAttribute('..project3'),
        approval_status=ApprovalStatus.APPROVED,
        time_correct=False,
        time_updates="My university has announced job placements, but I haven't signed a contract. I also don't expect to start my job until July. I can totally commit to 60 hours a week until then.",
    )

class InternSelectionScenario(ContributionsClosedScenario):
    """
    Create samples of the objects which matter once mentors have
    selected the interns they want to work with, and coordinators
    need to set funding sources for the selected interns.
    """
    round__start_from = 'mentor_intern_selection_deadline'

    intern_selection1 = factory.SubFactory(
        factories.InternSelectionFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant1'),
        project=factory.SelfAttribute('..project'),
        funding_source=InternSelection.UNDECIDED_FUNDING,
        organizer_approved=None,
        mentors=0,
    )
    intern_selection2 = factory.SubFactory(
        factories.InternSelectionFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant2'),
        project=factory.SelfAttribute('..project2'),
        funding_source=InternSelection.ORG_FUNDED,
        organizer_approved=True,
        mentors=0,
    )
    intern_selection3 = factory.SubFactory(
        factories.InternSelectionFactory,
        round=factory.SelfAttribute('..round'),
        applicant=factory.SelfAttribute('..applicant3'),
        project=factory.SelfAttribute('..project3'),
        funding_source=InternSelection.GENERAL_FUNDED,
        organizer_approved=False,
        mentors=0,
    )

    mentor_relationship1 = factory.SubFactory(
        factories.MentorRelationshipFactory,
        intern_selection=factory.SelfAttribute('..intern_selection1'),
        mentor=factory.SelfAttribute('..mentor_approval'),
    )
    mentor_relationship2 = factory.SubFactory(
        factories.MentorRelationshipFactory,
        intern_selection=factory.SelfAttribute('..intern_selection2'),
        mentor=factory.SelfAttribute('..mentor_approval2'),
    )
    mentor_relationship3 = factory.SubFactory(
        factories.MentorRelationshipFactory,
        intern_selection=factory.SelfAttribute('..intern_selection3'),
        mentor=factory.SelfAttribute('..mentor_approval3'),
    )

class InternshipWeekScenario(InternSelectionScenario):
    """
    Create the scenario where it's the start of the given week during the
    internship.
    """

    class Params:
        week = 1

    round__start_from = 'internstarts'
    round__days_after_today = factory.LazyAttribute(
        lambda round: -7 * (round.factory_parent.week - 1)
    )

    # Make sure two intern selections have been approved, and one is not approved.
    intern_selection1__organizer_approved = True
    intern_selection1__funding_source = InternSelection.ORG_FUNDED
