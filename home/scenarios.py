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
    # NOTE - update README.md if you change the documentation for this class
    """
    The `NewRoundScenario` scenario represents the time when the Outreachy organizers first set dates for the new internship round. No communities have signed up to participate yet.

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.

    This scenario will also create the following database objects:
     - Internship round (`class RoundPage`) with dates and deadlines. The internship round will be created such that the date the community CFP opens (`RoundPage.pingnew`) is set to today.
     - Open source community (`class Community`). The community name will be randomly generated.
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
    # NOTE - update README.md if you change the documentation for this class
    """
    The `CommunitySignupUnderwayScenario` scenario represents the time when community coordinators are signing communities up to participate in Outreachy. One mentor has submitted their project.

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
     - Mentor (username 'mentor1')

    This scenario will also create the following database objects:
     - The community will be marked as being approved to participate in the current internship round (`class Participation`).
     - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
     - One project has been submitted (`class Project`) by mentor1 for this community. The project has been approved by the coordinator. The project title will be randomly generated.

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
    # NOTE - update README.md if you change the documentation for this class
    """
    The Outreachy application period has two distinct periods: the initial application period and the contribution period. During the initial application period, applicants submit an eligibility form and essays (an initial application).

    The `InitialApplicationsUnderwayScenario` scenario represents the time during which applicants submit their initial applications.

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
     - Mentor (username 'mentor1')
     - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

    This scenario will also create the following database objects:
     - The community will be marked as being approved to participate in the current internship round (`class Participation`).
     - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
     - One project has been submitted (`class Project`) by mentor1 for this community. The project has been approved by the coordinator. The project title will be randomly generated.
     - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
     - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
     - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
     - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
     - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules

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
    # NOTE - update README.md if you change the documentation for this class
    """
    The Outreachy application period has two distinct periods: the initial application period and the contribution period. Applicants with an approved initial application will move onto the contribution period. Approved applicants will pick a project (or two), contact mentors, work on project tasks (contributions), and record those contributions in the Outreachy website.

    The `ContributionsUnderwayScenario` scenario represents the time during which applicants communicate with mentors and work on project contributions.

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
     - Mentors (usernames 'mentor1' to 'mentor3')
     - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

    This scenario will also create the following database objects:
     - The community will be marked as being approved to participate in the current internship round (`class Participation`).
     - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
     - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
     - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
     - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
     - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
     - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
     - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
     - A contribution (`class Contribution`) has been recorded by applicants applicant1 and applicant2
     - A final application (`class Contribution`) has been started by applicant1
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
    # NOTE - update README.md if you change the documentation for this class
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
    # NOTE - update README.md if you change the documentation for this class
    """
    Once the contribution period ends, it is time for Outreachy mentors to select their interns. Coordinators will assign a funding source to each intern. Outreachy organizers will coordinate with mentors if there is an intern selection conflict between two projects. Outreachy organizers will review all interns and approve or reject them.

    The `InternSelectionScenario` scenario represents the time just after the contribution period closes.

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
     - Mentors (usernames 'mentor1' to 'mentor3')
     - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

    This scenario will also create the following database objects:
     - The community will be marked as being approved to participate in the current internship round (`class Participation`).
     - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
     - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
     - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
     - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
     - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
     - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
     - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
     - A contribution (`class Contribution`) has been recorded by applicants applicant1, applicant2, applicant3, and applicant8
     - A final application (`class Contribution`) has been submitted by applicants applicant1, applicant2, applicant3, and applicant8
     - Interns have been selected (`class InternSelection`):
       - applicant1 has been selected as an intern to work with mentor1 (`class MentorRelationship`). The coordinator has not assigned a funding source for this internship. This internship is not yet approved by the Outreachy organizers.
       - applicant2 has been selected as an intern to work with mentor2 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
       - applicant3 has been selected as an intern to work with mentor3 (`class MentorRelationship`). The coordinator has requested that this internship be funded by the Outreachy general fund. This internship is not yet approved by the Outreachy organizers.
    """
    round__start_from = 'mentor_intern_selection_deadline'

    contribution1 = factory.SubFactory(
            factories.ContributionFactory,
            project=factory.SelfAttribute('..project'),
            applicant=factory.SelfAttribute('..applicant1'),
            round=factory.SelfAttribute('..round'),
    )
    contribution2 = factory.SubFactory(
            factories.ContributionFactory,
            project=factory.SelfAttribute('..project2'),
            applicant=factory.SelfAttribute('..applicant2'),
            round=factory.SelfAttribute('..round'),
    )
    contribution3 = factory.SubFactory(
            factories.ContributionFactory,
            project=factory.SelfAttribute('..project3'),
            applicant=factory.SelfAttribute('..applicant3'),
            round=factory.SelfAttribute('..round'),
    )

    finalapplication1 = factory.SubFactory(
            factories.FinalApplicationFactory,
            project=factory.SelfAttribute('..project'),
            applicant=factory.SelfAttribute('..applicant1'),
            round=factory.SelfAttribute('..round'),
    )
    finalapplication2 = factory.SubFactory(
            factories.FinalApplicationFactory,
            project=factory.SelfAttribute('..project2'),
            applicant=factory.SelfAttribute('..applicant2'),
            round=factory.SelfAttribute('..round'),
    )
    finalapplication3 = factory.SubFactory(
            factories.FinalApplicationFactory,
            project=factory.SelfAttribute('..project3'),
            applicant=factory.SelfAttribute('..applicant3'),
            round=factory.SelfAttribute('..round'),
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

class InternshipWeekScenario(InternSelectionScenario):
    # NOTE - update README.md if you change the documentation for this class
    """
    Each week during the internship, the Outreachy organizers have different tasks, emails to send, and intern chats to run.

    The `InternshipWeekScenario` scenario will show you the website dashboard as it looks to the Outreachy organizers during each week of the internship.

    Relevant dates are:

    This scenario creates the following accounts:
     - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
     - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
     - Mentors (usernames 'mentor1' to 'mentor3')
     - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

    This scenario will also create the following database objects:
     - The community will be marked as being approved to participate in the current internship round (`class Participation`).
     - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
     - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
     - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
     - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
     - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
     - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
     - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
     - A contribution (`class Contribution`) has been recorded by applicants applicant1, applicant2, applicant3, and applicant8
     - A final application (`class Contribution`) has been submitted by applicants applicant1, applicant2, applicant3, and applicant8
     - Interns have been selected (`class InternSelection`):
       - applicant1 has been selected as an intern to work with mentor1 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
       - applicant2 has been selected as an intern to work with mentor2 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
       - applicant3 has been selected as an intern to work with mentor3 (`class MentorRelationship`). The coordinator requested the internship be funded by the Outreachy general fund. However, the funding was denied, and the internship was not approved.

    Which internship week you want depends on what part of the code you're working on. For example, if you wanted to see the changes you've made to the intern welcome email template, you would want to set the week to the first week.

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
