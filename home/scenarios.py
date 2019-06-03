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


class ApplicationsOpenScenario(NewRoundScenario):
    """
    Create samples of the objects which matter once applicants are allowed to
    begin applying to participate in the new round.
    """

    round__start_from = 'appsopen'

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

class InternSelectionScenario(ApplicationsOpenScenario):
    """
    Create samples of the objects which matter once mentors start to
    select the interns they want to work with, and coordinators
    need to set funding sources for the selected interns.
    """

    round__start_from = 'mentor_intern_selection_deadline'
    sponsorship__amount = 13000

    mentor2 = factory.SubFactory(factories.MentorFactory)
    mentor3 = factory.SubFactory(factories.MentorFactory)

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

class WeekNineScenario(InternSelectionScenario):
    """
    Create the scenario where it's the start of week 9 during the internship.
    """

    round__start_from = 'internstarts'
    round__start_date =  datetime.date.today() - datetime.timedelta(weeks=9-1)

    # Make sure two intern selections have been approved, and one is not approved.
    intern_selection1__organizer_approved = True
    intern_selection1__funding_source = InternSelection.ORG_FUNDED
