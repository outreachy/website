Background
---

This document describes how the email notifications for the Outreachy website
work for Outreachy organizers, coordinators, and mentors.

Each section describes how a particular role experiences email notifications.
Each section has a list of emails that will be sent. Email sending is triggered
when a Django object that inherits from the ApprovalStatusAction class changes
approval status.

The actions that trigger an email to subscribe a mentor to the mailing list are
tricky. Outreachy organizers have to say they trust the coordinator (the
coordinator is approved) before the coordinator is subscribed to the mentors
mailing list. Once a coordinator is approved, any mentors the coordinator
approves should be subscribed to the mailing list.

Since mentors start out as approved for new Projects (so that they can edit
them), mentors shouldn't be added to the mailing list until their Project and
Coordinator is approved.


Mentor Workflow
---

Emails:

 EM1. Project changes status to PENDING
      - Send email to Project approvers (the community coordinators) to review
      - Use email template home/templates/home/email/project-review.txt

 EM2. Project changes status to APPROVED
      - Send email to Project submitters (the approved mentors) for next steps
      - Use email template home/templates/home/email/project-approval.txt

 EM3. MentorApproval changes status to PENDING
      - Send email to mentor approvers (the community coordinators) to review
      - Use email template home/templates/home/email/mentor-review.txt

 EM4. MentorApproval changes status to APPROVED
      - Send email to MentorApproval submitters (the approved mentors) for next steps
      - Use email template home/templates/home/email/mentor-approval.txt

 EM5. Project and Participation status is APPROVED:
      - Subscribe all approved mentors to the mentors mailing list
      - Use email template home/templates/home/email/mentor-list-subscribe.txt

New Project, New Mentor
===

1. Mentor submits a new project proposal.
   - A new MentorApproval is created, with the approval status set to APPROVED
     (so that the mentor can edit the project proposal).
   - A new Project is created, with the approval status set to PENDING.
   - EM1 is sent

2. Coordinators approve the project proposal.
   - Project approval status is set to APPROVED
   - EM2 is sent
   - EM5 is sent if the Participation status is APPROVED for this community.

Pending Project, New Co-Mentor
===

1. Co-mentor signs up to mentor this project.
   - A new MentorApproval is created, with the approval status set to PENDING
   - EM3 is sent

2. Coordinator approves the co-mentor.
   - MentorApproval status is set to APPROVED
   - No email is sent, since this project isn't approved

3. Coordinator approves Project.
   - Project status set to APPROVED.
   - EM2 is sent to all approved mentors.
   - EM5 is sent if the Participation status is APPROVED for this community.

Approved Project, New Co-Mentor
===

1. Co-mentor signs up to mentor this project.
   - A new MentorApproval is created, with the approval status set to PENDING
   - EM3 is sent

2. Coordinator approves the co-mentor.
   - MentorApproval status is set to APPROVED
   - EM4 is sent
   - EM5 is sent if the Participation status is APPROVED for this community.


Coordinator Workflow
---

The coordinator sign up process is similar to a mentor sign up process, but with
the added complexity that coordinators can sign up to be a mentor for a
community that has participated in a past round.

Emails:

 EC1. Participation changes status to PENDING
      - Send email to Participation approvers (the Outreachy organizers) to review
      - Use email template home/templates/home/email/community-signup.txt

 EC2. Participation changes status to APPROVED
      - Send email to Participation submitters (the approved coordinator) for next steps
      - Use email template home/templates/home/email/community-approved.txt

 EC3. CoordinatorApproval changes status to PENDING
      - Send email to coordinator approvers (the Outreachy organizers) to review
      - Use email template home/templates/home/email/coordinator-review.txt

 EC4. CoordinatorApproval changes status to APPROVED
      - Send email to CoordinatorApproval submitters (the Outreachy organizers) for next steps
      - Use email template home/templates/home/email/coordinator-approved.txt

 EC5. CoordinatorApproval and Participation status is APPROVED:
      - Subscribe all approved coordinators and approved mentors for the
        community under this round to the mentors mailing list
      - Use email template home/templates/home/email/mentor-list-subscribe.txt

New Community, New Coordinator
===

1. Coordinator submits a new community.
   - A NewCommunity is created.
   - A new Participation is created, with the approval status set to PENDING.
   - A new CoordinatorApproval is created, with the approval status set to APPROVED
     (so that the coordinator can edit the participation and community information).
   - EC1 is sent

2. Coordinators approve the new community.
   - Participation status is set to APPROVED
   - EC2 is sent
   - EC5 is sent to all approved coordinators
   - EM5 is sent to all approved mentors with approved projects in this
     commmunity.

Pending Community, New Co-Mentor
===

1. Co-coordinator signs up to coordinate this community.
   - A new CoordinatorApproval is created, with the approval status set to PENDING
   - EC3 is sent

2. Outreachy organizer approves the co-coordinator.
   - CoordinatorApproval status is set to APPROVED
   - No email is sent, since this project isn't approved

3. Organizer approves the community.
   - Participation status set to APPROVED.
   - EC2 is sent to all approved mentors.
   - EC5 is sent to all approved coordinators
   - EM5 is sent to all approved mentors with approved projects in this
     commmunity.

Approved Community, New Co-coordinator
===

1. Co-coordinator signs up to coordinate this community.
   - A new CoordinatorApproval is created, with the approval status set to PENDING
   - EC3 is sent

2. Coordinator or organizer approves the co-mentor.
   - CoordinatorApproval status is set to APPROVED
   - EC4 is sent
   - EC5 is sent

Past Community, New Coordinator
===

1. Coordinator signs up to coordinate this community.
   - A new CoordinatorApproval is created, with the approval status set to PENDING
   - EC3 is sent

2. Coordinator or organizer approves the co-mentor.
   - CoordinatorApproval status is set to APPROVED
   - EC4 is sent
   - EC5 is sent

Proceed to the "Past Community, Approved Coordinator" section

Past Community, Approved Coordinator
===

1. Coordinator signs up this community to participate in this round.
   - A new Participation is created, with the approval status set to PENDING
   - EC1 is sent

2. Organizers approves the community to participate.
   - Participation status is set to APPROVED
   - EC2 is sent
   - EC5 is sent
   - EM5 is sent to all approved mentors with approved projects in this
     commmunity.
