New Coordinator Flow
----

[Page] Community participation status in this round.
 * Intro paragraph says, if you don't see your community on this page, or
   you're a new community, sign up to participate here.

[Page] Sign up to be a participating community
 * Fill out at least new community information
 * Can also fill out information for the applicants and this round if they want

Wait for an email from the Outreachy organizers saying you're approved.

Existing Coordinator Flow
----

[Page] Community participation status in this round.
 * Find your community, click 'Participate in this round',
   * log in, Django recognizes you as an existing coordinator
   * create an account, Django says you're not listed as a coordinator
     * email sent to Outreachy organizers and listed coordinators

[Page] Edit community data
 * Update any questions you want to ask volunteers, mentors, or applicants
 * Update the Call for Volunteers text for this round
 * Update mentor project selection criteria description for this round
 * Update information on volunteers positions that are open

Coordinator emails mailing list with call for volunteers, and sends email to known mentors to tell them to sign up on the call for volunteers page.

Organizers get an email alert with information the community provided on funding
Organizers approve community for X number of interns after all funding discussion has completed.

Community status (not exclusive):
 * Unclaimed - coordinator has not said the community wants to participate
 * Looking for volunteers - coordinator has claimed listing, CFP for mentors is out
 * Closed to projects - it's two weeks before the deadline, and no new Outreachy projects can be added
 * Funded - Outreachy organizers have approved the community for X number of interns
 * Staffed - community has at least one mentor and project that has been approved

Once a community has the status set of [Funded AND Staffed], and the date is between the application period opening and closing, the community will appear on the rounds page.

Volunteer Flow
----

[Page] Call for volunteers and mentors
 * Create account or login
 * Fill out the form, submit

Coordinator is emailed
Coordinator can (optionally) approve volunteer to read applications
 * Volunteer emailed with instructions for how to view applications

If a volunteer later comes up with a project idea, they can submit to be a mentor through the [Page] Call for volunteers and mentors

Mentor Flow
----

[Page] Call for volunteers and mentors
 * Create account or login
 * Fill out the form with mentor information and project information, click submit

Coordinator is emailed
Coordinator approves mentor's project, or replies back to the email to give the mentor feedback (set In-reply-to to be the mentor)

Organizers must approve projects for Outreachy that have any of the following characteristics:
 * How long has the project accepted contributions from external contributors?
   * 0-3 months
   * 3-6 months
   * 6-12 months
 * How many people are currently contributing to this project?
   * 1-3 people
   * 3-5 people
   * 5-10 people
 * The date is two weeks before the application deadline

Once project is approved by coordinator (and organizer if necessary):
 * Mentor is added to mentors mailing list
 * Mentor gets new mentor email
 * Email includes instructions for how co-mentors can sign up
 * Mentor is given permission to view applications related to their project

Project title only is posted on the community page with an 'Apply to co-mentor' and status of project

Co-mentor or surrogate mentor flow
----

[Page] Project page or Community page
 * Click 'Apply to co-mentor this project'

[Page] Sign up to be a mentor
 * Fill out the form with just mentor information, click submit

Coordinator is emailed
Coordinator approves co-mentor
 * Co-mentor is added to mentors mailing list
 * Co-mentor gets new mentor email
 * Email includes instructions for how other co-mentors can sign up
 * Email includes instructions for how to propose another project, go to [Page] Project proposal
 * Co-mentor is given permission to view applications related to their project


Removing mentors from projects
----

When logged in, mentors can visit their [Page] Project page. There will be a 'resign as a mentor' button. If all mentors resign from a project, the project will be moved to 'no longer accepting new applicants'. The coordinator will be notified, as well as all applicants who applied to that project.

Static data all projects share
----

* General information on how to start contributing - e.g. from [Fedora's page](https://fedoraproject.org/wiki/Outreachy/2017)
* How to use IRC and IRC etiquette - e.g. from [Fedora's page](https://fedoraproject.org/wiki/Outreachy/2017) or [Outreachy's page](https://wiki.gnome.org/Outreachy/IRC)

Data to Gather
----

1. Collaborator (base profile for a coordinator, mentor, or volunteer):
   * Full name
   * nickname (e.g. "Hi, I'm [nickname]" or "Greetings, [nickname]")
   * Email
   * (Optional) pronouns
   * (Optional) 200x200 avatar picture
   * (Optional) What timezone are you normally in?
   * (Optional) What language(s) do you speak? (beginner/intermediate/fluent)

2. Each Outreachy community will have at least one coordinator (who may also be a mentor).
   Coordinators need to approve mentors and volunteers for their community.
   * Collaborator info

3. Coordinators need to provide information about their community:
 * For new community approval:
   * Name
   * Short description (3 sentences for someone who has never heard of your community or the technologies involved)
   * Website URL
   * How big is your community?
   * What different organizations and companies participate in the project?
   * Community open source license file URL
   * Do you rely or build upon proprietary software? Please elaborate.
   * (Optional) What is the community make-up with respect to volunteer and paid contributors?
   * (Optional) What is the community governance?
   * (Optional, shared with applicants) Code of Conduct URL
   * (Optional, shared with applicants) CLA URL
   * (Optional, shared with applicants) DCO URL - note that a DCO that requires contributors to use their full legal name can mean that trans contributors cannot participate, since it may be expensive or impossible to change their birth name
 * Static community info (enter once, probably never modify from round to round):
   * Name
   * Description of community
   * Communication channels for mentors and coordinators
   * (Optional) Email to reach all coordinators and mentors
   * (Optional) Description or links to documentation/tutorials for how new contributors get started.
   * (Optional) Link to your bug/issue tracker's "easy" or "newcomer friendly" bugs/features.
   * (Optional) Community blog or planet
   * (Optional) Community contributor list (e.g. contributors.debian.org)
   * (Optional) Community mentor list (e.g. mentors.debian.net) 
 * Information specific to this round:
   * What organization(s) do you expect to be able to provide funding for your community interns?
   * How many interns do you expect to fund for this round?
   * Blurb for [Page] Call for Volunteers and Mentors
   * (Optional) Additional questions to ask volunteers
   * (Optional) Additional questions to ask mentors
   * (Optional) Additional questions to ask applicants during the application process
 * Community status, internal, some states not exclusive:
   * Unclaimed - coordinator has not said the community wants to participate
   * Looking for volunteers - coordinator has claimed listing, CFP for mentors is out
   * Closed to projects - it's two weeks before the deadline, and no new Outreachy projects can be added
   * Funded - Outreachy organizers have approved the community for X number of interns
   * Staffed - community has at least one mentor and project that has been approved

4. For each volunteer that wants to apply to a community for a particular round, the organizers and coordinators need to know:
   * How long have you been contributing to the community?
   * What is your current community role?
   * What sub-projects do you work on?
   * What help can you provide the applicants or interns?
   * Are you willing to review and give feedback on applications?

5. For each potential mentor that wants to apply to a community for a particular round, the organizers and coordinators need to know:
   * How long have you been contributing to the community?
   * What is your current community role?
   * What is your mentorship style?
   * Have you read the mentor page and understand the process of being a mentor?
   * Are you available for 5-10 hours a week for mentoring during the internship period?
   * Are you available for 5 hours a week during the application period?
   * Are you aware that you will need to sign a mentor contract?

6. Coordinators and Outreachy organizers need know information about projects, such as:
 * Information for the coordinators and mentors:
   * Benefits of the project to the intern
   * Importance of the project to the community
   * How long has the project accepted contributions from external contributors? (Note that new projects without a community are not allowed for Outreachy projects, but may be approved for GSoC.)
     * 0-3 months
     * 3-6 months
     * 6-12 months
     * 1-2 years
     * > 2 years
   * How many people are contributing to this project currently?
     * 1-3 people
     * 3-5 people
     * 5-10 people
     * 11-20 people
     * 21-50 people
     * 50-100 people
     * > 100 people
 * Information for the applicants:
   * Short title (nine words or less, assuming the person has never heard of your technology before, starting with an adverb like "Create", "Improve", "Extend", "Survey", "Document")
   * Description
   * URL for project repository or contribution pages
   * URL for project issue/bug tracker
   * Project communication channels
   * (Optional, shared with applicants) Code of Conduct URL
   * (Optional, shared with applicants) CLA URL
   * (Optional, shared with applicants) DCO URL - note that a DCO that requires contributors to use their full legal name can mean that trans contributors cannot participate, since it may be expensive or impossible to change their birth name
   * Technology interns will work with, or skills they will use or develop:
     * Skill or technology name
     * Required or optional for applicants
     * level of expertise for applicants: we'll teach you, beginner, moderate, advanced
     * FIXME: Not sure how to handle sub-projects here - e.g. front-end/back-end -
       each subproject may have different skills
   * How should applicants find a task to contribute to?
   * Are you willing to work with ineligible interns? Some applicants may not be
     eligible due to school commitments. Selecting 'No' will hide your contact
     information from these applicants, so that you will only work with applicants
     can be selected as interns. We recommend setting this to 'No' unless you have a
     lot of spare bandwidth.
   * List project for applicants of:
     * Outreachy
     * Google Summer of Code (must be a programming project)
     * Both
   * Is the project currently accepting new applicants?
   * Project status:
     * Waiting on coordinator approval
     * Waiting on organizer approval
     * Approved to participate
     * Not eligible for participation

New pages to create
----

[Page] List of all past and current participating FOSS communities in Outreachy
* Page shows the status of whether a community is going to participate

* Possible status:
  * Not participating
  * Will participate (coordinator is still working on call for volunteers page)
  * Open to volunteers (call for volunteers/mentors page ready to accept)
  * Closed to new Outreachy projects (two weeks before the application deadline)

* Clicking the status button will either take you to:
  * Coordinator edit page or Notify me when this community signs up
  * Sign up to be notified of Call for Volunteers
  * Volunteer sign up page

[Page] Sign up to be a participating community
 * Forces login or account creation
 * The page should have both a 'Save' and 'Submit for moderation' button
 * Coordinators should get periodic email reminders if they have Saved but not Submitted a community

[Page] Edit community data
 * Forces login or account creation
 * The page should have both a 'Save' and 'Submit for moderation' button
 * Coordinators should get periodic email reminders if they have Saved but not Submitted a community

[Page] Community status or call for volunteers and mentors
 * State is unclaimed:
   * Notify me when this community signs up
   * Sign up to be a community coordinator
 * State is claimed and community information has been edited and submitted:
   * Community status: (waiting on funding, coordinators are, etc...)
   * Propose a new project -> login -> mentor/project sign-up
   * Lists any submitted projects
   * 'Apply to co-mentor this project' -> login -> mentor sign-up
   * Project status:
     * Waiting on coordinator approval
     * Waiting on organizer approval
     * Approved to participate
     * Not eligible for participation

[Page] Notify me when this community signs up
 * Forces login or account creation
 * Organizers should have some insight into communities that have mentors but no coordinator - possibly as part of a dashboard?

[Page] Sign up to be a volunteer or mentor
 * Forces login or account creation
 * The page should have both a 'Save' and 'Submit for moderation' button
 * Mentors and volunteers should get periodic email reminders if they have Saved but not Submitted their information

[Page] Project proposal
 * Forces login or account creation
 * The page should have both a 'Save' and 'Submit for moderation' button
 * Mentors should get periodic email reminders if they have Saved but not Submitted their project

[Page] Community landing page
 * Customized link and CSS for GSoC communities

[Page] Project page
 * Details hidden - please apply as an Outreachy applicant to see details
 * Customized link and CSS for GSoC communities
 * 'Apply to co-mentor this project' -> login -> mentor sign-up
