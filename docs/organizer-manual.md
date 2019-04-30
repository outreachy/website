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

## Invoicing

### Billing Information

During the intern selection period is a good time to ask for billing information for sponsors. The email template for that is in the organizer private GitLab notes repo.

We use Invoice Ninja to track invoices, their status, and internship credits for future round. We do *not* send invoices using the Invoice Ninja interface. Only save invoices as a draft.

### Community Credits

Community or sponsor credits happen in a number of ways:

 * Sometimes a community is billed early for a specific number of interns. If a community wants to accept less interns then they were billed for, there will be a credit.
 * Some sponsors that are grandfathered in only want to donate to a particular community. If that community accepts less interns than they have sponsorship for, there will be a credit.
 * Some sponsors that are grandfathered in only want to donate to intern funding for any communities. If we have less interns that were accepted for the Outreachy general fund, there will be a credit.
 * An intern fails, and we don't send them their internship stipend. The remaining stipends that were not send (e.g. mid-point or final stipend) is recorded as a community credit.

Credits are recorded as an "Expense" in Invoice Ninja. The "Project" is the community (or any interns) that the credit should go towards. The private notes sections documents how much the sponsor was originally invoiced for, the invoice number, the remaining credit, and which communities in which round we've already used this funding for.

Before invoicing a community for this round, always check in Invoice Ninja expenses to see if they have a credit.

## Adding Draft Invoices

Make sure to add the sponsor contact details and invoice draft to Invoice Ninja. There is a particular format for setting the invoice number that makes it easier to search: `RoundDate-InvoiceNumber-CommunitiesThatReceiveThisFunding`. If an invoice spans multipe rounds, add the second round after the invoice number. That way when you search for all sponsors that donated to a particular round, the past invoice will show up.

Keep track of the status of the invoice in the private notes field. Note when it was sent to Conservancy. Change the invoice sent date to be the Friday after intern selection announcement. If the sponsor wants to be invoiced later than that, set the sent date to be in the future.

## Sponsorship Logos

When Outreachy announces the accepted interns, we should have all sponsor logos displayed on the [Outreachy website homepage](https://www.outreachy.org) with the right prominance for their sponsorship amount. Sponsorship levels are on the [sponsorship page](https://www.outreachy.org/sponsor).

You can edit the logos on the homepage by going to the [Wagtail admin interface](https://www.outreachy.org/admin/) choosing 'Pages' from the sidebar, and clicking the pencil icon for the first page that shows up. Add a logo by clicking the plus button between logos in the right sponsorship level section. Use the image uploader to upload an image, and tag it with 'sponsor logo' and 'sponsor'. You can search for logos we've used in the past that are already uploaded.

Sponsor logos are stored in the GitLab private notes repository, under `graphics/sponsor-logos`.

## Sponsor Twitter Handles

When we announce the accepted Outreachy interns, we want to thank our sponsors on Twitter. This requires collecting sponsor Twitter handles. Some are recorded in Invoice Ninja in the 'Clients' priviate notes. Most are missing because there's an obvious Twitter handle to use. Some open source communities have no handle, in which case we just include their text name.

Some sponsors have a yearly donation. We credit their sponsorship level each round as half the amount of their yearly sponsorship. Some sponsors are rounded up to the next sponsorship level if the amount is very close (e.g. within a thousand dollars or so). Check the past history of the home page to see how those yearly sponsors have been credited, or just leave their logos in the same place.

We create an individual tweet, thanking each ceiling smasher and equalizer sponsors. All Promotor sponsors are thanked in one tweet. Includer sponsors all get thanked in one or two tweets.

General format:

 * `Congratulations to the NUMBER interns accepted for the @outreachy ROUND internships! https://www.outreachy.org/alums/`
 * The @outreachy internships wouldn't be possible without the support of our sponsors.
 * Thank you to the Outreachy Ceiling Smasher sponsor @HANDLE! We appreciate their [commitment to/continued support towards] @outreachy, and improving diversity in free and open source software.
 * We'd like to thank our Equalizer sponsor @HANDLE! It's awesome to see COMPANY supporting diversity in free and open source software.
 * A big thank you goes to our Equalizer sponsor @HANDLE! We appreciate their continued support of @outreachy and diversity in free and open source software.
 * Outreachy is so thankful for our Promoter sponsors @HANDLE, @HANDLE, @HANDLE, and @HANDLE. Thank you for supporting diversity in free and open source software!
 * Outreachy would also like to thank our Includer sponsors @HANDLE, @HANDLE, @HANDLE, @HANDLE, @HANDLE, and @HANDLE.

## Invoice and Logo Prep

Once all Outreachy interns have been accepted or rejected by the Outreachy organizers, it's time for prepping invoices, getting sponsor logo prominence correct, and creating the draft Twitter announcement tweets.

The process is:

 * Go to the [Outreachy dashboard](https://www.outreachy.org/dashboard) and confirm that every intern selection that is marked as being funded by community sponsors has a corresponding invoice in Invoice Ninja. Ensure the amount of sponsorship is correct. Some communities have more funding earmarked for them than they will accept interns. Most communities don't want to be invoiced for future interns, but some do. Check with the community coordinator. If the community already has been invoiced, or wants to be invoiced for more interns then they accepted, record the community credits in the 'Expenses' section. Record which community the credit is for in the project field of the expense.
 * *Record past used credits* Look at all interns who are marked for general funding sponsorship. Look through the past credits for 'Any intern'. Apply those past credits by recording in the notes which community intern and round they went to. If a credit is completely used, mark it as paid and archive it.
 * *Apply sponsor funding for any intern* Look at sponsors for this round who wanted to sponsor any interns. Note in the private notes which communities and round that went to.
 * *Record new community credits* If a sponsor's funding for any intern for this round was not used, record it as a credit in the 'Expenses' section under the 'Any intern' project. Sponsors who donate to the Outreachy general fund without a stipulation that it go towards intern funding don't need to be recorded as a credit.
 * *Delete unused invoices* If a community had sponsorship and they haven't been billed, but they won't accept any interns this round, delete the invoice. This involves comparing the community names in the invoice numbers to the list of all interns marked for community sponsor funding.
 * *Fix sponsor logo prominence on Outreachy website* Now that the invoice list is finalized, filter the list by this round date (e.g. 2019-05). That will filter on the invoice number. Sort by sponsor name and then sort again by sponsor amount. Go through the website and ensure all sponsors are credited at the right prominence.
 * *Remove old sponsor logos* Compare the list of sponsors on the Outreachy website. Remove any sponsors that aren't being invoiced this round. Double check the Conservancy svn repository in the `Agreements/Sponsorship` folder for any yearly sponsorship agreements. Ensure you don't delete a yearly sponsor that is receiving credit for half their sponsorship this round.

## Invoicing Sponsors

When invoicing sponsors, always check the invoice sending date and notes field. Some sponsors need to be invoiced at a later date. Otherwise, invoice all community-specific sponsors after the interns have accepted the internship. We don't want to invoice a sponsor and then have the intern not accept the internship and have to credit the community. General funding sponsors can be invoiced at any time.

Ask Software Freedom Conservancy to invoice the sponsor, and they will send the invoice. Instructions for the format and email address to send to are in the GitLab notes repository in the `payment-emails.txt` file and `email/email-sponsor-confirmation.txt`. Mark the invoice as sent in Invoice Ninja when you make the invoice request. Mark in the invoice private notes the date you sent the invoice request. Once Conservancy sends the invoice, update the sent and due date to reflect the actual invoice dates.

Conservancy does not update their request tracker ticket with when the invoice has been paid. Sometime during the year, they will update their ledger file to indicate when the invoice has been paid. The ledger file is in `Ledger/outreachy.ledger`. You can use this command to look at the accounts receivable entries in ledger: `ledger -V -f Ledger/outreachy.ledger --group-by date register /^Accrued:Accounts\ Receivable/` 

Once the ledger shows the invoice amount as a negative amount in Accrued:Accounts Receivable:Outreachy, it means Conservancy has recorded the invoice as paid. Once the invoice shows up in ledger as being paid, then enter payment for the invoice in Invoice Ninja for that specific date in ledger.
