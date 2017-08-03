# What is Outreachy?

Outreachy is a three-month paid internship program for people traditionally underrepresented in tech.
This particular project is an attempt to rebuild a new website for Outreachy.

# Current state of Outreachy tech

The Outreachy web presence is scattered across multiple different sites, domains, and technologies:
 - [GNOME Outreachy homepage](https://www.gnome.org/outreachy/) - shell homepage, where the outreachy.org domain currently redirects to
 - [GNOME wiki Outreachy pages](http://wiki.gnome.org/Outreachy) - moinmoin based wiki with information about how to apply and sponsor
 - [Outreachy application system](http://outreachy.gnome.org) - PHP-based application system currently hosted on OpenShift
 - irc.gnome.org #outreachy - GNOME IRC channel - where applicants get help
 - [Outreachy Planeteria](http://www.planeteria.info/outreach) - blog aggregation for Outreachy interns

Missing things:
 - An Outreachy coordinator blog
 - A user-friendly chat system (IRC ports are often blocked by universities due to concerns about IRC being used for spam bot coordination)
 - A way for coordinators, mentors, and interns to update the information we have stored and/or displayed (without all needing GNOME wiki accounts)

# Goals

 - Move Outreachy web presence onto our own domain, outreachy.org
 - Create templates for pages that have a standard layout (e.g. round pages) to eliminate manually updating multiple pages when a date changes
 - Create data models to track information about communities, mentors, sponsors, applicants, and interns
 - Use those data models to send emails (e.g. mentor needs to select an intern, remind mentor to send intern feedback, etc)

## Stretch Goals

 - Allow community coordinators and mentors to create and manage community and project pages
 - Replace the current Outreachy application system with one that integrates into this site
 - Replace planetaria with one hosted on our domain (that allows for filtering which blogs are displayed?)
 - Track longitudinal information of alumni, so we can share success stories and improve our program
 - Track where communities are in our "funnel" - e.g. do they have funding? a landing page? which mentors are signed up in the application system?
 - Track sponsorship information
 - Create a better way of displaying the list of potential Outreachy projects - e.g. allow searching, tagging for programming language or design or documentation or user experience

# Technology Choices

We evaluated a couple different choices:
 - CiviCRM
 - Wordpress
 - Red Hen
 - Django

CiviCRM proved too clunky to use, and ultimately their data model didn't necessarily fit our data models. Wordpress might have been fine with a template plugin and would have good user experience, but with everything we wanted to do, we felt we would ultimately outgrow Wordpress.

There are other proprietary tools for tracking sponsorship information, but since Outreachy is a project under the Software Freedom Conservancy and the Outreachy organizers believe in the power of free and open source, we have decided not to use proprietary software wherever possible.

Django fit our needs for flexibility, data model definition, and future use cases. However, the Django admin interface is pretty clunky and intimidating. We wanted to have a very easy way for all our organizers to quickly edit content. The Wagtail CMS plugin provides a nice user interface and template system, while still allowing programmers to fully use Django to implement models. It also provides internal revision tracking for page content, which means we can easily roll back content changes from the wagtail admin web interface if necessary.
