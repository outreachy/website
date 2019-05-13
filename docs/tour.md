settings directory
 outreachyhome/settings/
typically settings/base.py, sometimes in dev.py or production.py

Django will create some directories so that it can serve up the site locally. Don't commit files from those directories. `git ls-tree HEAD` will show you which directories are under revision control

docs - documentation
contacts - the contract form for organizers
home - most of the website code
outreachyhome - base website pages, settings
search - not used (was part of the sample wagtail project)

class RoundPage
https://github.com/outreachy/website/blob/master/home/models.py#L139

RoundPage terminology is inconsistent with the rest of the site: "orgs"/"organizations" should be "communities"

this class has functions - most functions are just used in templates
https://github.com/outreachy/website/blob/master/home/models.py#L188

class Comrade - extension of Django's user model
https://github.com/outreachy/website/blob/master/home/models.py#L728

a newly-registered account does not have a Comrade; that's created (hopefully soon) after registration by directing them to /account/. some views require that the logged-in person have a Comrade, so those inherit from ComradeRequired, which redirects to /account/ first if they haven't done that yet.

RoundPage.objects.latest('internstarts') - this is code that needs to be modified

Wagtail (Content Management System) - pages managed this way don't exist in git, they only exist in the live site's database, so your local development copy won't have them.

Most views will have a URL pattern in:
https://github.com/outreachy/website/blob/master/home/urls.py

Let's take a look at the code for https://www.outreachy.org/apply/project-selection
We'll find the right view by looking at urls.py
https://github.com/outreachy/website/blob/master/home/urls.py#L6

(Other URLs may be found in other urls.py - look at the comment at the top of urls.py)

The current project selection page view is here:
    https://github.com/outreachy/website/blob/master/home/views.py#L735

Terminology:
    - Outreachy organizers (Sage, Marina, etc) - Django user model has is_staff set to True
    - internship rounds - RoundPage
    - communities - class Community - e.g. Debian, Fedora
    - communities participate in an internship round - class Participation
    - each community has one or more coordinators - class CoordinatorApproval
    - community mentors provide projects - class Project
    - mentors are associated with a project - class MentorApproval


Test database - provided by Django - sets up new empty database for testing

We want to write tests, but we need to be able to create dummy data to fill in the objects:

https://github.com/outreachy/website/blob/master/home/factories.py

uses https://factoryboy.readthedocs.io/en/latest/ - add this link to our documentation

Looking at tests:
    https://github.com/outreachy/website/blob/master/home/test_roundpage.py

we subclass TestCase from Django, which subclasses Python's unittest TestCase class - you may have to look at either documentation to figure out what a function is doing.

https://docs.python.org/3/library/unittest.html
https://docs.djangoproject.com/en/1.11/topics/testing/tools/

The test client - pretend to make HTTP requests to any views, using the test database

Sending email

email templates - the first line of the template will be the subject - white space is stripped off the beginning and end of the rest of the template and used as the email body

https://github.com/outreachy/website/blob/master/home/email.py

When a mentor wants to co-mentor a project, the coordinator will get an email saying they should review the mentor and approve it:
https://github.com/outreachy/website/blob/master/home/templates/home/email/mentorapproval-pending.txt

Some email functions automatically find the right template by using the model name and approval status e.g. mentorapproval-pending.txt:
    https://github.com/outreachy/website/blob/master/home/email.py#L47
