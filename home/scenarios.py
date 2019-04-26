"""
Meta-factories which combine the individual factories from factories.py to set
up complete scenarios which are useful for various testing purposes.
"""

import factory
from . import factories
from home.models import ApprovalStatus

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
