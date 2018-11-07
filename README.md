# What is Outreachy?

Outreachy is a three-month paid internship program for people traditionally underrepresented in tech.
This particular project is an attempt to rebuild a new website for Outreachy.

# Current state of Outreachy tech

The Outreachy web presence is scattered across multiple sites, domains, and technologies:
 - [GNOME Outreachy homepage](https://www.gnome.org/outreachy/) - shell homepage, where the outreachy.org domain currently redirects
 - [GNOME wiki Outreachy pages](http://wiki.gnome.org/Outreachy) - moinmoin based wiki with information about how to apply and sponsor
 - [Outreachy application system](http://outreachy.gnome.org) - PHP-based application system currently hosted on OpenShift
 - irc.gnome.org #outreachy - GNOME IRC channel - where applicants can get assistance
 - [Outreachy Planeteria](http://www.planeteria.info/outreach) - blog aggregation for Outreachy interns

Missing things:
 - An Outreachy coordinator blog
 - A user-friendly chat system (IRC ports are often blocked by universities due to concerns about IRC being used for spam bot coordination)
 - A way for coordinators, mentors, and interns to update the information we have stored and/or displayed (without all needing GNOME wiki accounts)

# Goals

 - Move the Outreachy web presence onto our own domain, outreachy.org
 - Create templates for pages that have a standard layout (e.g. round pages) to eliminate manually updating multiple pages when a date changes
 - Create data models to track information about communities, mentors, sponsors, applicants, and interns
 - Use these data models to send emails (e.g. mentor needs to select an intern, remind mentor to send intern feedback, etc)

## Stretch Goals

 - Allow community coordinators and mentors to create and manage community/project pages
 - Replace the current Outreachy application system with one that integrates into this site
 - Replace planetaria with one hosted on our domain (that allows for filtering which blogs are displayed?)
 - Track longitudinal information of alumni, so we can share success stories and improve our program
 - Track where communities are in our "funnel" - e.g. do they have funding? a landing page? which mentors are signed up in the application system?
 - Track sponsorship information
 - Create a more efficient way of displaying potential Outreachy projects - e.g. allow: searching, tagging for programming language, design, documentation, or user experience

# Technology Choices

We evaluated a couple different choices:
 - CiviCRM
 - Wordpress
 - Red Hen
 - Django

CiviCRM proved to be too clunky to use, and their data model did not perfectly fit our data models. Wordpress might have been fine with a template plugin and would offer a good user experience, but with our current objectives, we felt we would ultimately outgrow Wordpress.

There are other proprietary tools for tracking sponsorship information, but we have decided not to use proprietary software where possible. This decision is due to Outreachy's involvement under the Software Freedom Conservancy and Outreachy's belief in the power of free and open source software. 

Django fit our needs for flexibility, data model definition, and future use cases. However, the Django admin interface is difficult to use and intimidating. It is essential that all organizers have a very easy way to quickly edit content. The Wagtail CMS plugin provides a nice user interface and template system, while still allowing programmers to fully use Django to implement models. Wagtail also provides internal revision tracking for page content, meaning content changes can easily be rolled back from the wagtail admin web interface if necessary.

# How does the Outreachy website tech work together?

The Outreachy website is built in [Python](https://www.python.org/) and on a web framework called [Django](https://www.djangoproject.com/). Additionally, the Outreachy website uses a content management system called [Wagtail](https://wagtail.io/), which builds on top of Django. [Dokku](http://dokku.viewdocs.io/dokku/) is run on the Outreachy webserver which allows us to deploy new code, manage our Let's Encrypt SSL certificates, and backup the Outreachy website database. Outreachy organizers are the oly users permitted ssh access to push new code to the server.

# Optional helpful background reading

[Django topic guides](https://docs.djangoproject.com/en/1.11/topics/), particularly the [models](https://docs.djangoproject.com/en/1.11/topics/db/models/) guide.

# Setting up your development environment

Django can be run locally to test: changes to the code, creating new pages, adding new users, etc. Local tests that are run will not impact the main Outreachy website, only the local version of the website. Please test changes locally before submitting a pull request.

To set up the local development environment, first clone the repository to a local machine:

```
git clone https://github.com/sagesharp/outreachy-django-wagtail.git
```

To develop with Python the installation of Python 3 development headers is required. If the system is on Debian Linux, install nodejs 8 or install the `nodejs-legacy` package, due to older versions of the package installing as `node` rather than `nodejs`.

Next, create a new virtualenv. A "virtualenv" is a separate virtual environment for working on different Python projects. It is good practice to create a virtual environment for each Python project in case there are conflicting dependencies, and so that all dependencies are recorded on each project.

The following instructions will create a new virtualenv that will have all the necessary python packages installed for the Outreachy website. We use [pipenv](https://pipenv.readthedocs.io/en/latest/) for this purpose.

To install pipenv, use [install Homebrew](https://brew.sh/) (if on a Mac or Windows) or (running Linux) [install Linuxbrew](http://linuxbrew.sh/).

Then [install pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv).

The following command will automatically create a virtual environment, and install the Python dependencies specified in the `Pipfile`. To get help with pipenv, run `pipenv --help`

```
pipenv install
```

Pipenv records changes to the project's dependencies in the `Pipfile` when packages are added/removed with these commands:

```
pipenv install <package>
```

```
pipenv uninstall <package>
```

Activate the virtual environment by typing the following command in the directory of the project:

```
pipenv shell
```

In addition to the Python packages that were installed when the virtualenv was created, other Node.js packages are needed. These packages will be placed in a `node_modules` directory inside the project folder. Make sure `npm` is installed, then run:

```
npm install
```

If this is the first local version of the website for testing, the website database will need to be initialized. The following command will create a new database with models on the Outreachy website. The database will initially have no website pages, but will eventually store local test pages.

```
./manage.py migrate
```

The next step is to create an admin account for the local website.

```
./manage.py createsuperuser
```
# Testing the local website

Once the above set up commands have been run, the local website will be ready for testing. Run this command to start the Django webserver and serve up the local website:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py runserver
```

In a web browser, go to `http://localhost:8000/admin/` to get to the Wagtail administrative interface. `http://localhost:8000/django-admin/` will load the regular Django administrative interface. Log into both on the account you created with `./manage.py createsuperuser`. 

To create participating communities, project proposals etc. start by setting up a `RoundPage`. This can be done easily from the *Django administrative interface*. First, navigate to `http://127.0.0.1:8000/django-admin/home/roundpage/add/`, login with the `superuser` account and fill out the necessary fields: `path`,`depth`,`title`,`slug`,`content-type` (should be `round page`), `owner`, `page title` and `Roundnumber`. All other fields can be run with the defaults. Afterwards navigate to `http://127.0.0.1:8000/communities/cfp/` and view the current round. 

# Django shell

Django has a 'shell' mode to run snippets of Python code, which is extremely useful for figuring out why view code is not working. The 'shell' is also useful for doing quick tests of how templates (especially email templates) will look.

Run the shell on either the local copy of the database, or on the remote server's database. To start the shell on the local code and database run:

```
./manage.py shell
```

A Python prompt will appear that looks fairly similar to the standard Python shell, except that all the Django code will be available. For instance, try importing all the models in `home/models.py`:

```
$ ./manage.py shell
Python 3.6.6 (default, Jun 27 2018, 14:44:17) 
[GCC 8.1.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from home.models import *
```

Say we are changing an email template, and want to know whether the template will render correctly. We will use the template `home/templates/home/email/interns-notify.txt` as an example. This template takes an InternSelection object and a RoundPage object, both of which will be passed in a dictionary to the render function. Lets pick the first InternSelection object in the list:

```
>>> intern_selection = InternSelection.objects.all()[0]
```

Now, two objects can be passed to render and get the HttpResponse. This will change any instances of the objects in the template so they use the values of the fields referenced. The render function takes an HTTP request object. If necessary, a simple dictionary can be created for use as the render object. In this example, we pass in None for the request object, because the email template doesn't require it.

```
>>> response = render(None, 'home/email/interns-notify.txt', { 'current_round' : intern_selection.round(), 'intern_selection' : intern_selection, 'coordinator_names': intern_selection.project.project_round.community.get_coordinator_names(), },)
```

How the final template will look is viewable by getting content out of the HttpResponse object and decoding it:

```
>>> print(response.content.decode('utf-8'))
```

Remember, if any of the Python code is changed, to restart and reload the code exit the shell (CTRL-d).

# Tour of the code base

Django breaks up functionality into a project (a Django web application) and apps (a smaller set of Python code that implements a specific feature). There is only one project deployed on a site at a time, but there could be many apps deployed. Read more about what an application is in [the Django documentation](https://docs.djangoproject.com/en/2.0/ref/applications/).  
In the Outreachy repository, the directory `outreachy-home` is the project. There are several apps:
* `home` which contains models (based on wagtail) used on the Outreachy home pages
* `search` which was set up during the wagtail installation for pages and media searching 
* `contacts` which is a Django app for the contact page.

The Outreachy website also uses some apps that are listed in the `INSTALLED_APPS` variable in `outreachyhome/settings/base.py`, but are not found in top-level directories in the repository. This is because the application's code was installed into the virtualenv directory when `mkvirtualenv -r requirements.txt` was run. The command looked at the Python package requirements listed in requirements.txt and ran `pip install` for each of them. For example, if the virtualenv name is `outreachy-django` and Python 2.7 is being run locally, code for Wagtail forms (wagtail.wagtailforms) can be found in `~/.virtualenvs/outreachy-django/lib/python2.7/site-packages/wagtail/wagtailforms`.

The top-level directory `docs` is where the maintenance and design documents go.

Running Django to test locally, may create two directories `static` and `media`. These will store site images and media uploaded through the local site. These directories are in the .gitignore file and should never be committed.

# Adding a new app

If there is a set of Django models, views, and templates that are used for a discrete chunk of functionality, it is advised to create a new app in the top-level directory. For example, to call the new app `contacts` run the helper script and set up the app:

```
./manage.py startapp contact
```

This script will stick boilerplate examples in a new directory:

```
$ ls contacts/
admin.py  apps.py  __init__.py  migrations  models.py  tests.py  views.py
```

A `templates` directory may need to be added to that app:

```
makedir contacts/templates
```

# Dokku logs

If the test server was deployed with Django debugging settings turned on, Django will send all emails to the console. To create new test users, extract the verification URL from the log. This can be done by running:

```
ssh -t dokku@outreachy.org logs test
```

# Sentry error logging

Outreachy uses Sentry to log error messages received on both the Outreachy website and the test website. Unfortunately, that means if dokku is ever used to start the Python shell on the remote website, any typos end up getting reported to Sentry. To suppress those error messages, unset the `SENTRY_DSN` environment variable by running:

```
ssh -t dokku@www.outreachy.org run www env --unset=SENTRY_DSN python manage.py shell
```

# Rolling back migrations

If the database has been migrated (either locally or on the server) to go back to a previous database migration, the following command can be run:

```
./manage.py migrate home [version number]
```

# Delicate migrations

Sometimes a field does not work exactly as intended and needs to be changed. In this example, a BooleanField will be changed to a CharField to support three different values. The values in the old field need to be preserved to populate the contents of the new field.

1. Define the new CharField. Set 'null=True' in the argument list.

2. Run `./manage.py makemigrations && ./manage.py migrate`

3. Create an empty migration: `./manage.py makemigrations home --empty`

4. Edit the new empty migration file. This can be done by defining a new function that takes `apps` and `schema_editor`, like it is documented in the `0005_populate_uuid_values.py` file in the [Django "Writing a migration" documentation.](https://docs.djangoproject.com/en/1.11/howto/writing-migrations/). The objects for that Model can be accessed, and a new field based on values in the old field can be set. Make sure to add the function to the operations list. Note that some class members that represent the choice short code in the database may need to be copied into the migration, because all migrations only have access model class members that are Django fields (like CharField or BooleanField).

5. Remove the `null=True` argument from your model, and delete the old field. The field may need to be removed from admin.py and the views. Then run `./manage.py makemigrations && ./manage.py migrate` which will generate a third migration to make sure the field must be non-null, but the second migration will set the field on all objects. When Django prompts about changing a nullable field to a non-nullable field, choose 'Ignore for now'.

6. The third migration will fail if someone has added a new model object between the second migration and the third migration. In this case, roll back to the first migration (where the field was first added). Pass the migration number to go back to: `./manage.py migrate home PREFIX` this should be a unique prefix (like the first four numbers of the migration). Then try to run the migration again: `./manage.py migrate`. Repeat as necessary.
