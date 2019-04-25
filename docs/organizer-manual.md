This manual will document the common tasks that an Outreachy organizer has during the Outreachy application phase and internship.

# Organizer private resources

 * Public GitHub [Outreachy website repository](https://github.com/sagesharp/outreachy-django-wagtail/)
 * Public etherpad for taking notes during Outreachy organizer meetings (ask an organizer for the URL before the meeting)
 * Private GitLab [notes repository](https://gitlab.com/sagesharp/outreachy-notes/) for organizers
 * Private GitLab [eligibility notes repository](https://gitlab.com/sagesharp/outreachy-applicant-review)
 * Private Software Freedom Conservancy [subversion repository](svn+ssh://svn@basswood.sfconservancy.org/Conservancy/Projects/Outreachy) for storing intern and mentor agreements, sponsorship agreements, and the Outreachy finances ledger files. Only Outreachy PLC members have access to this via ssh key.
 * Invite-only [Zulip chat](https://chat.outreachy.org/) for Outreachy interns, mentors, coordinators, and organizers
 * [Invoice Ninja account](https://www.invoiceninja.com/) for tracking invoices
 * [Organizer dashboard](https://www.outreachy.org/dasboard/) for sending semi-automated emails and tracking progress during the internship round
 * [Rackspace account](https://mycloud.rackspace.com/) for managing Outreachy web servers

# Intern selection period

After final applications are closed, the following steps need to be taken:

 - Mentors select one or more interns for their project
 - Coordinators set the funding source for each intern
 - Outreachy PLC members approve or reject any general funding requests
 - Outreachy organizers approve or reject any additional interns

## Coordinating with Google Summer of Code

If the internship aligns with Google Summer of Code, some Outreachy applicants may have applied for both Outreachy and Google Summer of Code.

If the applicant applied for the same project under both programs, or even the same community but a different project, Outreachy organizers generally let Outreachy community coordinators handle talking with the GSoC org admin.

If the applicant has applied for a community that isn't participating in Outreachy, we try to coordinate with that community. Ideally, they would let us contact the applicant and ask which program they want to work under. That's not always possible, as some GSoC orgs want to stick with the Google Summer of Code rule to not talk about their intern selections until the announcement date.

The Outreachy final application has a question about which GSoC orgs the person is applying to, and what the mentor's contact info is. There's an email template in the Organizer's private GitLab notes repo for contacting the community.

## Intern Selection Checking

When reviewing all interns, please do the following:

 * **Resolve any intern conflicts** The Outreachy website will email all project mentors and coordinators when an intern is selected by more than one project. Go to the organizer's email and facilitate any conversation around that conflict. Sometimes an intern has made substantially more contributions to one project. In that case, ask whether the other mentor is okay with the applicant being accepted under the other project. If the mentors can't make a decision, then you can email the applicant to ask them to choose.
 * **Review applicant strength** Applicants with a ranking of 2 ("Inexperienced - smaller contributions that vary in quality") or below should not be accepted. If the intern was marked as a 3 ("Good - some smaller contributions of good quality"), review their contributions and amount of time available for the internship. If their contributions are minor one-liners and they have less than 2/3rds of the internship period free (typically less than 60 / 90 days free), then we may not want to accept them. Following up with the mentors about the strength of the applicant can be informative, since sometimes applicants have made contributions that they didn't record them in the website.
 * **Review applicant time commitments** Click the applicant's name on the dashboard to be taken to their detailed application and time commitment information. If an applicant said they would quit their job, email them to a) double check if their stated weekly hours is correct and b) double check whether they will quit that job, if required. It's required that applicants quit their jobs if they work more than 20 hours a week, or if they're working in a technical role and they're being accepted for a technical position. There's an email template in the Outreachy organizer's private GitLab eligibility repository that you can use.
 * **Check final applications for mentions of jobs or other time commitments** Sometimes applicants aren't truthful, and don't include all their time commitments on their initial application. If you notice they mention a job or classes, email them with a sternly worded warning and ask questions about their time commitments.
 * **Check for mentors over-committing themselves** Review all the mentors in each community. If one mentor has selected two interns, ask if they have a co-mentor who can help them. If they don't, and the community is new to Outreachy, tell them they shouldn't select more than one intern.

## Invoice Information Gathering

During the intern selection period is a good time to ask for billing information for sponsors. The email template for that is in the organizer private GitLab notes repo.

Make sure to add the sponsor contact details and invoice draft to Invoice Ninja. There is a particular format for setting the invoice number that makes it easier to search: `RoundDate-InvoiceNumber-CommunitiesThatReceiveThisFunding`. Do not click send invoice! Save it as a draft instead.  Ask Software Freedom Conservancy to invoice the sponsor, and they will send the invoice. Instructions for the format and email address to send to are in the GitLab notes repository in the `payment-emails.txt` file and `email/email-sponsor-confirmation.txt`. Mark the invoice as sent when you make the invoice request. Mark in the invoice private notes the date you sent the invoice request.

Once the invoice is sent and ledger shows the invoice amount as a negative amount in Accrued:Accounts Receivable:Outreachy, it means Conservancy has recorded the invoice as paid. You can use this command to look at the accounts receivable entries in ledger: `ledger -V -f Ledger/outreachy.ledger --group-by date register /^Accrued:Accounts\ Receivable/`
