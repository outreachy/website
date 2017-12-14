This contact form is a little different than the default one the `contact_form` app supplies.
That application assumes you want to always send email with a From header set to the same email address.
It also assumes you want to apply a template to the body of the email, such as recording the location of the contact form and person's contact information.

This doesn't fit Outreachy organizers' needs. We want to have an email sent to us as if the person just sent a normal email, in order to cut down on the amount of time editing out the template, remembering to change the To field from the default email to their email, etc. So, we wanted to extend the contact app to send email from the Django server as if the person had sent email themselves.

This involves using the name and email address that the person specified in the contact form in the From header. This is essentially header forgery.

Initially, we were concerned that larger email providers like Google would classify the Outreachy mail server as a spammer if we set the From header to visitor-supplied values. This is only a concern for mail to the mentors mailing list, because mail sent to the Outreachy organizers doesn't leave our internal mail server.

Fortunately, two significant signals those email providers use are in fact not forged when the message passes through our Mailman mailing lists.

First, SPF checks the SMTP envelope-from address against DNS records; for the outgoing list mail, the envelope-from address is the Mailman bounce address at outreachy.org, and outreachy.org's SPF policy in DNS says that our mail server is permitted to send mail from that domain, so that should always pass.

Second, the DKIM signature that the Outreachy mail server adds asserts that the message came from outreachy.org and that certain headers (including From) have not been tampered with since then. The outreachy.org DNS records will confirm that the signature is valid, and recipients don't check whether the key used to sign the message belongs to the domain of the putative sender specified in the From address.
