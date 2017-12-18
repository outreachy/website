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

# How does the Outreachy website tech work together?

The Outreachy website is built on a [Python](https://www.python.org/) and a web framework called [Django](https://www.djangoproject.com/). Additionally, the Outreachy website uses a content management system called [Wagtail](https://wagtail.io/), which builds on top of Django. On the Outreachy webserver, we run [Dokku](http://dokku.viewdocs.io/dokku/), which helps us deploy new code, manage our Let's Encrypt SSL certificates, and backup the Outreachy website database. Only Outreachy organizers have ssh access to push new code to the server.

# Optional helpful background reading

[Django topic guides](https://docs.djangoproject.com/en/1.11/topics/), particularly the [models](https://docs.djangoproject.com/en/1.11/topics/db/models/) guide.

# Setting up your development environment

You can run Django locally to test changes to the code, test creating new pages, test adding new users, etc. The local tests you run will not impact the main Outreachy website, only your local version of the website. You should test changes locally before submitting a pull request.

To set up your local development environment, first clone the repository to your local machine:

```
git clone https://github.com/sagesharp/outreachy-django-wagtail.git
```

Next, you'll need to create a new virtualenv. A "virtualenv" is a separate virtual environment for working on different Python projects. It's good practice to create a virtual environment for each Pyton project you're working on, in case they have conflicting dependencies, and so that you make sure to record all the dependencies for each project.

These instructions will help you create a new virtualenv that will have all the python packages installed that you need to work on the Outreachy website. We use the `-r` option to specify where the file is that contains the list and version numbers of Python packages to install in the virtual environment. The `-a` option means that when you activate the virtual environment, you will automatically change directories to the directory where the repository source code was cloned. If you need help understanding the mkvirtualenv command, run `mkvirtualenv --help`

```
mkvirtualenv -a ~/PATH/TO/outreachy-django-wagtail -r ~/PATH/TO/outreachy-django-wagtail/requirements.txt outreachy-django
```

Now, you activate the virtual environment by typing the following command:

```
workon outreachy-django
```

If this is your first time creating a local version of the website for testing, you'll need to set up the local website database from scratch. The following command will create a new database with the models in the Outreachy website. The database will initially have no website pages, but will eventually store your local test pages.

```
./manage.py migrate
```

The next step is to create an admin account for the local website.

```
./manage.py createsuperuser
```
# Testing the local website

Once you've run the above setup commands, you should be all set to start testing your local website. First, run the command to start the Django webserver and serve up the local website.

```
./manage.py runserver
```

In your web browser, go to `http://localhost:8000/admin/` to get to the Wagtail administrative interface.

# Tour of the code base
Django breaks up functionality into a project (a Django web application) and apps (smaller a set of Python code that implements a specific feature). There is only one project deployed on a site at a time, but there could be many apps deployed. You can read more about what an application is in [the Django documentation](https://docs.djangoproject.com/en/2.0/ref/applications/).  
In the Outreachy repository, the directory `outreachy-home` is the project. We have several apps:
* `home` which contains models (based on wagtail) used on the Outreachy home pages
* `search` which was set up during the wagtail installation to allow searching for pages and media
* `contacts` which is a Django app for our contact page.

The Outreachy website also uses some apps that are listed in the `INSTALLED_APPS` variable in `outreachyhome/settings/base.py`, but aren't found in top-level directories in the repository. That's because the apps' code was installed into your virtualenv directory when you ran `mkvirtualenv -r requirements.txt`. That command looked at the Python package requirements listed in requirements.txt and ran `pip install` for each of them. For example, if your virtualenv name is `outreachy-django` and you're running Python 2.7 locally, you'll be able to find the code for Wagtail forms (wagtail.wagtailforms) in `~/.virtualenvs/outreachy-django/lib/python2.7/site-packages/wagtail/wagtailforms`.

The top-level directory `docs` is where our maintenance and design documents go.

If you've been running Django to test locally, you may have two directories `static` and `media`. These will store site images and media you've uploaded through your local site. These directories are in the .gitignore file and should never be committed.

# Adding a new app

If you have a set of Django models, views, and templates that is a discrete chunk of functionality, you may want to create a new app in the top-level directory. If we want to call our new app `contacts` we can run the helper script to set up our app:

```
./manage.py startapp contact
```

That script will stick some boilerplate examples in a new directory:

```
$ ls contacts/
admin.py  apps.py  __init__.py  migrations  models.py  tests.py  views.py
```

You may need to add a `templates` directory to that app:

```
makedir contacts/templates
```

# Rolling back migrations

If you have migrated the database (either locally or on the server) and want to go back to a previous migration, you can run:

```
./manage.py migrate home [version number]
```
