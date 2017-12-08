New Coordinator Flow
----

[Page] Community participation status in this round.
 * Intro paragraph says, if you don't see your community on this page, or
   you're a new community, sign up to participate here.

[Page] Sign up to be a participating community

Wait for an email from the Outreachy organizers saying you're approved.

Existing Coordinator Flow
----

[Page] Community participation status in this round.
 * Find your community, click 'Participate in this round',
   * log in, Django recognizes you as an existing coordinator
   * create an account, Django says you're not listed as a coordinator
     * [Page] Notify me when this community signs up

[Page] Edit community data
 * Update any questions you want to ask volunteers, mentors, or applicants
 * Update the descriptions of the project criteria
 * Update information on volunteers positions that are open

Coordinator emails mailing list with call for volunteers, and sends email to known mentors to tell them to sign up on the call for volunteers page.

Organizers get an email alert with information the community provided on funding
Organizers approve community for X number of interns after all funding discussion has completed.

Django - once community has information, has an approved mentor and one project, and the organizers have approved the community for the number of interns, and the application period is open, the community is listed on the project page

Volunteer Flow
----

[Page] Call for volunteers and mentors
 * Create account or login
 * Fill out the form, submit

Coordinator is emailed
Coordinator can approve volunteer to read applications
 * Volunteer emailed with instructions for how to view applications

Mentor Flow
----

[Page] Call for volunteers and mentors
 * Create account or login
 * Fill out the form with just mentor information, click submit

Coordinator is emailed
Coordinator approves mentor to propose projects
 * Mentor is added to mentors mailing list
 * Mentor gets email to submit a project idea

[Page] Project proposal
 * Mentor fills out project information

Coordinator is emailed
Coordinator approves mentor's project, or replies back to the email to give the mentor feedback (set In-reply-to to be the mentor)

Mentor is given permission to view applications related to their project
Project is posted on the community page - but contact information is only visible to signed-in community mentors and volunteers until applications open (then open to signed in applicants who are eligible)
Mentor is emailed saying their project is approved
Give mentor a link to their project's public page, and a link for co-mentors to sign up

Co-mentor or surrogate mentor flow
----

[Page] Project page
 * Click 'Apply to co-mentor this project'

[Page] Call for volunteers and mentors
 * Fill out the form with just mentor information, click submit

Coordinator is emailed
Coordinator approves co-mentor, optionally approves them to propose other projects
 * Co-mentor is added to mentors mailing list

Co-mentor is emailed
You're now listed, mentor instructions, if you want to propose another project, go to [Page] Project proposal

Removing mentors from projects
----

When logged in, mentors can visit their [Page] Project page. There will be a 'resign as a mentor' button. If all mentors resign from a project, the project will be moved to 'no longer accepting new applicants'. The coordinator will be notified, as well as all applicants who applied to that project.

Static data all projects share
----

* General information on how to start contributing - e.g. from [Fedora's page](https://fedoraproject.org/wiki/Outreachy/2017)
* How to use IRC and IRC etiquette - e.g. from [Fedora's page](https://fedoraproject.org/wiki/Outreachy/2017) or [Outreachy's page](https://wiki.gnome.org/Outreachy/IRC)

Data to Gather
----

1. Outreachy organizers have a set of questions new communities need to answer:
   * Name
   * Description
   * Website
   * Name of coordinator(s)
   * Email of coordinator(s)
   * Pronouns for coordinator(s)
   * How big is your community?
   * What is the community make-up with respect to volunteer and paid contributors?
   * What different organizations and companies participate in the project?
   * What is the community governance?
   * Link to your community have a Code of Conduct?
   * What open source license is the project under?
   * Link to your project's CLA, if you have one. 
   * Do you rely or build upon proprietary software? Please elaborate.
   * Link to documentation for how new contributors get started.
   * Link to your bug/issue tracker's "easy" or "newcomer friendly" bugs/features.
   * What organization(s) do you expect to be able to provide funding for your community interns?
   * How many interns do you expect to fund for this round?

2. Each Outreachy community will have at least one coordinator (who may also be a mentor).
   Coordinators need to approve mentors and volunteers for their community.
   * Name
   * Email address
   * Pronouns

3. Coordinators need to provide information about their community:
   * Name
   * Description of community
   * Communication channels for mentors and coordinators
   * Getting started tutorials or documentation
   * Community blog or planet
   * Community contributor list (e.g. contributors.debian.org)
   * Community mentor list (e.g. mentors.debian.net) 
   * Email to reach all coordinators and mentors
   * Link to community's code of conduct

4. Coordinators need to provide information specific to this round:
   * What organization(s) do you expect to be able to provide funding for your community interns?
   * How many interns do you expect to fund for this round?
   * Additional questions to ask volunteers
   * Additional questions to ask mentors
   * Additional questions to ask applicants during the application process
   * Blurb for [Page] Call for Volunteers and Mentors

5. Coordinators and Outreachy organizers need know information about volunteers, such as:
   * Name
   * Email address
   * Pronouns
   * What timezone will you be in for the application period?
   * What language(s) do you speak? (beginner/intermediate/fluent)
   * How long have you been contributing to the project?
   * What help can you provide the applicants or interns?
   * Are you willing to review and give feedback on applications?

6. Coordinators and Outreachy organizers need know information about mentors, such as:
   * Name
   * Email address
   * Pronouns
   * What timezone will you be in for the application and internship period?
   * What language(s) do you speak? (beginner/intermediate/fluent)
   * What is your mentorship style?
   * How long have you been contributing to the project?
   * Have you read the mentor page and understand the process of being a mentor?
   * Are you available for 5-10 hours a week for mentoring during the internship period?
   * Are you available for 5 hours a week during the application period?

7. Coordinators and Outreachy organizers need know information about projects, such as:
   * Short title
   * Description
   * Benefits of the project to the intern
   * Importance of the project to the community
   * How many people are contributing to this project currently?
   * How long has each mentor been contributing to this project?
   * Link to project repository or contribution pages
   * Link to project issue/bug tracker
   * Project communication channels
   * Link to project's code of conduct
   * Does your project have a CLA or DCO that requires contributors to use their legal name?
     This can be an issue for trans contributors.
   * Technology interns will work with, or skills they will develop:
     * Skill or technology name
     * Required or optional for applicants
     * level of expertise for applicants: we'll teach you, beginner, moderate, advanced
     * FIXME: Not sure how to handle sub-projects here - e.g. front-end/back-end -
       each subproject may have different skills
   * How should applicants find a task to contribute to?
   * Willing to work with ineligible interns? Some applicants may not be
     eligible due to school commitments. Selecting 'No' will hide your contact
     information from these applicants, so that you will only work with applicants
     can be selected as interns. We recommend setting this to 'No' unless you have a
     lot of spare bandwidth.
   * Is the project currently accepting new applicants?
   * Is the project eligible for Google Summer of Code? (Only programming projects are eligible.)


New pages to create
----

[Page] List of all past and current participating FOSS communities in Outreachy
* Page shows the status of whether a community is going to participate

* Possible status:
  * Not participating
  * Will participate (coordinator is still working on call for volunteers page)
  * Open to volunteers (call for volunteers/mentors page ready to accept)

* Clicking the status button will either take you to:
  * Coordinator edit page or Notify me when this community signs up
  * Sign up to be notified of Call for Volunteers
  * Volunteer sign up page

[Page] Sign up to be a participating community

[Page] Edit community data

[Page] Notify me when this community signs up
 * Linked to from participating community pages when someone logs in or creates an account and they aren't a coordinator
 * Organizers should have some insight into communities that have mentors but no coordinator - possibly as part of a dashboard?

[Page] Call for volunteers and mentors

[Page] Project proposal

[Page] Community landing page
 * Customized link for GSoC communities

[Page] Project page
 * Customized link for GSoC communities
