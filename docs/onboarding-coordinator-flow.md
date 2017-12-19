Background
---

The Outreachy community and mentor sign-up process currently involves too much manual labor
for Outreachy organizers. In order to allocate organizer time towards expanding the program,
working with applicants, and finding additional funding, we need to automate this process.

Updating Project Listings is Tedious
===

A year ago, we switched the Outreachy community page to list all projects and the skills
they required. This allowed applicants to quickly scan the list for projects that
included programming languages, tools, or skills they were interested in. Before this
change, Outreachy organizers would receive 5-10 emails each round from applicants
who were confused as to how to pick a project. Now the only emails we get are from
applicants who can't find a project that fits their needs.

The problem with listing projects is that Outreachy organizers needed to manually
update the community project list page against each participating FOSS community's page.
Just keeping the project listings up to date during the round takes approximately
10-15 hours per round.

Mentors Get Lost in On-boarding
===

A very common problem that leads to additional Outreachy organizer manual labor
is the mentor on-boarding process. Each Outreachy mentor needs to:
 * Receive a welcome email explaining how the process works and how to set a
   filter to ensure the mentor mailing list posts don't end up in the Gmail
   promotions tab
 * Be signed up for the mentors mailing list
 * Apply to be a mentor in the Outreachy application system
 * Be manually approved by the Outreachy organizers to be a mentor
 * Select their intern by navigating to the application and selecting "willing to mentor"
 * Go to their application profile and sign the mentor agreement

This manual process of mentor on-boarding and herding mentors towards the next
steps adds at least 6-10 hours per round.

We often lose mentors during the wait to be approved for the application system
by Outreachy organizers (who often have to ask coordinators about a mentor if
they aren't listed on the community landing page). This also adds additional
stress on organizers during the intern selection process, as all mentors who
want to select an intern must "claim" their intern in the application system
and sign the mentor agreement.

Projects Disappear in Six Months
===

In order for a FOSS community to participate in Outreachy, they need to have:
 * Funding for at least one intern
 * 1 coordinator
 * At least one mentor and project

There is usually six months between the first Call for Outreachy communities going out,
and when the internship starts. Projects often get completed in that time, or change
scope in such a way that it makes them unlikely to be appropriate for Outreachy interns.

Our coordinators have asked for a way to gather information on volunteers who are
willing to help guide Outreachy applicants, but may not necessarily have a project
in mind yet. Volunteers can sign up, and then coordinators can remind them closer to
the application process opening that they should submit a project.

Mentors Select Ineligible Applicants
===

Many mentors don't review applications in the system before selecting an
intern, which can lead them to select someone who isn't eligible or has
borderline time eligibility.

Applicants often fill out applications at the last minute, after working with a
mentor. We need to add a two step process: Applicants check their eligibility,
and then they start working with mentors.

We want mentors to be aware of who is eligible, so that they can focus early on
applicants who they can select as interns. We want the application system to be
something that helps mentors, not something they wrestle with at the last
minute. Adding a dashboard stating which applicants are eligible will help.

Unclear Project Descriptions Trigger Impostor Syndrome
===

There are also negative impacts to Outreachy applicants for each community
having a different landing page style.  Some project list both required and
optional skills, and other projects list skills without any indication whether
they are required or optional.  Some projects note that they'll teach
applicants and interns about a skill. 

This leads to confusion in applicants. Many Outreachy applicants have impostor
syndrome, and they won't apply for a project unless they have all the skills.
Additionally, most projects don't list what level of experience applicants need
for each skill.  This leads applicants to assume they need to be an "expert" in
a skill to apply. Many potential Outreachy applicants talk themselves out of
applying because mentors aren't clear about which skills are required,
optional, or teachable, and what skill level is needed.

Inappropriate Projects Added At the Last Minute
===

Finally, not all projects proposed by mentors are appropriate for Outreachy.

Outreachy projects need to have an established community, unlike the
student-created projects that GSoC allows. Outreachy's goal is to find open
source communities who have multiple people who can provide interns mentorship
and sponsorship. Interns learn how to work with an open source community,
rather than working solo on their own project.  An established FOSS community
provides interns networking opportunities and conferences they can attend or
speak at, which increases their chances of being hired to work on open source.
Student-created projects are unlikely to help with these goals.

The goal for Outreachy listing projects is to allow people who wouldn't
normally propose their own project to GSoC to apply for an internship. Another
requirement for Outreachy projects is that applicants must make at least one
contribution to the project (and most make many small contributions during the
application process).

Adding a new project a week or two before the application project doesn't give
enough time for all Outreachy applicants to have a fair chance at making a
contribution. Instead, late project additions are usually added for applicants
who already have connections with open source project mentors. This unduly
favors people who already have some experience contributing to open source,
which is more likely to be white, college-educated students.

We've had issues in the past with Outreachy mentors not understanding the
goals and requirements for Outreachy projects. By adding additional required
questions about the projects, Outreachy organizers can be notified of projects
that may not meet our requirements, and reject or accept those projects.

Solutions
===

This new coordinator, mentor, and volunteer on-boarding system will help these
issues by:

 * Pushing down mentor and volunteer approval from Outreachy organizers to
   community coordinators, who are in a better position to know whether the
   person should participate
 * Automatically collecting mentor and volunteer information
 * Automatically subscribing approved mentors and volunteers to the mentors
   mailing list and sending them a welcome onboarding email.
 * Providing a way for people to sign up as volunteers and proposing a project later
 * Only showing mentor and community contact information to signed in
   applicants who are eligible for this round (unless a project mentor wants to
   work with ineligible applicants)
 * Providing applicants clearer information about the skills they need to apply
 * Allowing Outreachy organizers to reject projects that aren't appropriate
   for Outreachy due to project newness, community size, or mentor inexperience
 * Forcing applicants to check their eligibility with an automated process
   before working with mentors. (goal by end of January)
 * Providing mentors with a dashboard with clear information of which
   applicants are eligible or borderline (goal by end of January)
 * Providing a community page for use with GSoC with all contact information
   and only listing projects appropriate to GSoC (stretch goal)

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
 * Fill out the form with mentor information and (optionally) project information, click submit
 * mentors who are not yet approved can also submit projects?

Coordinator is emailed - approves mentor
(Optional) Coordinator approves mentor's project, or replies back to the email to give the mentor feedback (set In-reply-to to be the mentor)

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
   * Will all projects involve contributing to software with an [OSI-approved open source license](https://opensource.org/licenses/alphabetical), or creative works with a [Creative Commons license](https://creativecommons.org/share-your-work/licensing-types-examples/)?
     * If no: Please detail your licenses, with links to license text.
   * Community open source license file URL (if all projects are under the same license)
   * Do you rely or build upon proprietary software? Please elaborate.
   * (Optional) What is the community make-up with respect to volunteer and paid contributors?
   * (Optional) What is the community governance?
   * (Optional, shared with applicants) Code of Conduct URL
   * (Optional, shared with applicants) CLA URL
   * (Optional, shared with applicants) DCO URL - note that a DCO that requires contributors to use their full legal name can mean that trans contributors cannot participate, since it may be expensive or impossible to change their birth name
 * Static community info (enter once, probably never modify from round to round):
   * Longer description of community
   * Communication channels for mentors and coordinators
   * (Optional) Email to reach all coordinators and mentors
   * (Optional) Description or links to documentation/tutorials for how new contributors get started.
   * (Optional) Link to your bug/issue tracker's "easy" or "newcomer friendly" bugs/features.
   * (Optional) Community blog or planet
   * (Optional) Community contributor list (e.g. contributors.debian.org)
   * (Optional) Community mentor list (e.g. mentors.debian.net)
   * (Optional) Link to community logo image (will be scaled to 200 pixels wide)
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
   * Does your project use an [OSI-approved open source license](https://opensource.org/licenses/alphabetical) or a [Creative Commons license](https://creativecommons.org/share-your-work/licensing-types-examples/)?
     * If no: Please detail your licenses, with links to license text.
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
* Timeline of this round (link to dates in most recent round page)
* Outreachy blurb, link to mentor and coordinator pages
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
 * Only users with community permissions can publish a new page
 * Logged in users can submit a community page for moderation (or 'Save draft' to come back to it later)
   * Implementation: possibly we could set a page signal on page save, and check the 'submitted_for_moderation' flag? Or just use Django instead of wagtail pages? Maybe use django-ckeditor for a RichText field?

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
