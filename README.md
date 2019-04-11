# What is Outreachy?

Outreachy is a three-month paid internship program for people traditionally underrepresented in tech.
This repository is for the Django code that comprises the [Outreachy website](https://www.outreachy.org).

# Current state of Outreachy tech

The Outreachy web presence is in a couple of different places:
 * [Outreachy website](https://www.outreachy.org)
 * [GitHub Repository](https://github.com/sagesharp/outreachy-django-wagtail/)
 * [Repository CI Status](https://travis-ci.org/sagesharp/outreachy-django-wagtail.svg?branch=master)

Older/deprecated websites include:
 - [GNOME Outreachy homepage](https://www.gnome.org/outreachy/) - shell homepage, where the outreachy.org domain currently redirects to
 - [GNOME wiki Outreachy pages](http://wiki.gnome.org/Outreachy) - moinmoin based wiki with information about how to apply and sponsor
 - [Outreachy application system](http://outreachy.gnome.org) - PHP-based application system currently hosted on OpenShift
 - irc.gnome.org #outreachy - GNOME IRC channel - where applicants get help
 - [Outreachy Planeteria](http://www.planeteria.info/outreach) - blog aggregation for Outreachy interns

# Future Long-term Goals

 - Replace planetaria with one hosted on our domain (that allows for filtering which blogs are displayed?)
 - Track longitudinal information of alumni, so we can share success stories and improve our program
 - Track sponsorship information
 - Create a better way of displaying the list of potential Outreachy projects - e.g. allow searching, tagging for programming language or design or documentation or user experience

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

In order to develop with Python, you'll need the Python 3 development headers, so install them. You'll also need to install node.js.

Next, you'll need to create a new virtualenv. A "virtualenv" is a separate virtual environment for working on different Python projects. It's good practice to create a virtual environment for each Python project you're working on, in case they have conflicting dependencies, and so that you make sure to record all the dependencies for each project.

These instructions will help you create a new virtualenv that will have all the python packages installed that you need to work on the Outreachy website. We use [pipenv](https://pipenv.readthedocs.io/en/latest/) for this purpose.

To install pipenv, you'll need to either [install Homebrew](https://brew.sh/) (if you're on a Mac or Windows) or (if you're running Linux) [install Linuxbrew](http://linuxbrew.sh/).

Then [install pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv).

The following command will automatically create a virtual environment and install the Python dependencies specified in the `Pipfile`. If you need help understanding pipenv, run `pipenv --help`

```
pipenv install
```

[Note: Pipenv automatically records changes in the project's dependencies in the `Pipfile` when you add/remove packages. You can add a package with the command `pipenv install <package>`. You can remove a package with the command `pipenv uninstall <package>`.]

Now, you activate the virtual environment by typing the following command in the directory of the project:

```
pipenv shell
```

In addition to the Python packages that were installed for you when you created the virtualenv, you also need to install some Node.js packages; these will be placed in a `node_modules` directory inside your project folder. Make sure you have `npm` installed, then run:

```
npm install
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
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py runserver
```

In your web browser, go to `http://localhost:8000/admin/` to get to the Wagtail administrative interface. `http://localhost:8000/django-admin/` takes you to the regular Django administrative interface. You can log in into both with the account you created with `./manage.py createsuperuser`. 

If you want to create participating communities, project proposals etc. you first need to set up a `RoundPage`. An easy way to do so is from the *Wagtail interface*. To do this navigate to `http://127.0.0.1:8000/admin` and login with the `superuser` account. On the left menu, click on `Pages` and then on the `Home` directory. Press `Add child page`, select `Round page` and fill out the necessary fields (such as `title`, `roundnumber`, `slug`). All other fields can be run with the defaults. Afterwards you can navigate to `http://127.0.0.1:8000/communities/cfp/` to see the current round.

# Django shell

Django has a 'shell' mode where you can run snippets of Python code. This is extremely useful for figuring out why view code isn't working. It's also useful for doing quick tests of how templates (especially email templates) will look.

You can run the shell on either your local copy of the database, or you can run it on the remote server's database. To start the shell on your local copy of the code and local database, run

```
./manage.py shell
```

You'll get a Python prompt that looks fairly similar to the standard Python shell, except that all the Django code you've written is available. For instance, you can import all the models in `home/models.py`:

```
$ ./manage.py shell
Python 3.6.6 (default, Jun 27 2018, 14:44:17) 
[GCC 8.1.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from home.models import *
```

Say we're making changes to an email template, and we want to know whether the template will render correctly. We'll use the template `home/templates/home/email/interns-notify.txt' as an example. This template takes an InternSelection object and a RoundPage object, both of which will be passed in a dictionary to the render function. Let's pick the first InternSelection object in the list:

```
>>> intern_selection = InternSelection.objects.all()[0]
```

Now, we can pass those two objects to render to get the HttpResponse. That will change any instances of the objects in the template to use the values of the fields referenced. The render function takes an HTTP request object. If you need to, you can create a simple dictionary to use as the render object. In this example, we pass in None for the request object, because the email template doesn't require it.

```
>>> response = render(None, 'home/email/interns-notify.txt', { 'current_round' : intern_selection.round(), 'intern_selection' : intern_selection, 'coordinator_names': intern_selection.project.project_round.community.get_coordinator_names(), },)
```

You can see how the final template will look by getting the content out of the HttpResponse object and decoding it:

```
>>> print(response.content.decode('utf-8'))
```

Remember, if you change any of the Python code, you'll need to exit the shell (CTRL-d) and restart it to reload the code.

# Tour of the code base

When you first clone this project, you'll see a couple top level directories:
 * `bin`
 * `contacts`
 * `docs`
 * `home`
 * `outreachyhome`
 * `search`

If you've followed the steps above to set up your development environment, Django may have generated some directories and put files in them. Don't modify or commit files from those directories. You can use `git ls-tree HEAD` to show you which directories are under revision control. Top-level directories you shouldn't commit to are ones like `media`, `node_modules`, and `static`. These directories are in the .gitignore file, so your changes to those files won't be listed if you run `git status`.

The `bin` directory almost never changes. It includes a script that's run by dokku before the website is deployed to outreachy.org.

The top-level directory `docs` is where our maintenance and design documents go. It also includes the intern and mentor agreements, and our privacy policy.

The `outreachyhome` directory contains the base HTML page templates for all pages on the website. It also includes all the Django project settings for both development and production environments. This directory isn't changed very often.

Django breaks up functionality into a project (a Django web application) and apps (smaller a set of Python code that implements a specific feature). There is only one project deployed on a site at a time, but there could be many apps deployed. You can read more about what an application is in [the Django documentation](https://docs.djangoproject.com/en/2.0/ref/applications/).  

In the Outreachy repository, the directory `outreachy-home` is the project. We have several apps:
* `home` which contains models used on most the Outreachy pages
* `search` which was set up during the wagtail installation to allow searching for pages and media
* `contacts` which is a Django app for our contact page

The Outreachy website also uses some apps that are listed in the `INSTALLED_APPS` variable in `outreachyhome/settings/base.py`, but aren't found in top-level directories in the repository. That's because the apps' code was installed into your virtualenv directory when you ran `mkvirtualenv -r requirements.txt`. That command looked at the Python package requirements listed in requirements.txt and ran `pip install` for each of them. For example, if your virtualenv name is `outreachy-django` and you're running Python 2.7 locally, you'll be able to find the code for Wagtail forms (wagtail.wagtailforms) in `~/.virtualenvs/outreachy-django/lib/python2.7/site-packages/wagtail/wagtailforms`.

## Outreachy terminology

Please use the gender-neutral ["they/them" pronouns](http://pronoun.is/they) and gender-neutral language to refer to all Outreachy participants.

 * **FOSS:** Free and Open Source Software.
 * **Project:** A series of intern tasks to improve FOSS.
 * **Community:** A community is a set of related projects. For instance, if Django participated as an Outreachy community, the community might mentor projects to improve Django core functionality, Django extensions, or Django documentation.
 * **Mentor:** A mentor defines a project. They work with applicants to help them complete contributions to the project during the application process. A mentor selects an applicant to be the intern for their project. The mentor works remotely with the selected intern during the internship. An intern can have one or more mentors. Most Outreachy mentors only mentor one intern.
 * **Coordinator:** Each internship project must be associated with a FOSS community participating in Outreachy. That community provides funding for interns, either directly from community funds, or by finding a company or foundation to sponsor interns. Each community has one or more coordinators, who review submitted projects, approve mentors, set internship funding sources, and generally provide a communication link between the mentors and Outreachy organizers. Some smaller communities have only one coordinator, who is also the only mentor.
 * **Outreachy organizers:** There is a small set of organizers who oversee the entire Outreachy program. They communicate with coordinators about funding, onboard new communities, review inern feedback, authorize intern payments, answer questions, and promote the program to potential applicants.
 * **Applicant:** During the application process, Outreachy applicants make contributions to projects and apply to be an Outreachy intern.
 * **Intern:** An accepted applicant works with a mentor for three months during the internship period.

## Outreachy Internship Phases

The Outreachy website changes depending on what phase of the internship round Outreachy is in. The phases of the internship round are:

 1. Community sign up and mentor project submission
 2. Initial application submission
 3. Applicant contribution period
 4. Final application submission period
 5. Intern selection period
 6. Intern announcement
 7. Internship period

Some of these phases overlap. For example, the project submission period ends part-way through the applicant contribution period. Since Outreachy internships run twice a year, that means one internship round may overlap with another. For example, the end of the intership period often overlaps with the community sign up and mentor project submission phase.

## Project submission objects

The Outreachy internship round is represented by `class RoundPage` in `home/models.py`. It contains dates that define the phases of the internship rounds, the round name, the round number, links to future intern chats over video and text.

A FOSS community is represented by the `class Community` in `home/models.py`. It contains things like the community name.

Communities can participate in multiple Outreachy internship rounds. We record their participation in each round in with the `class Participation` in `home/models.py`. A participation includes details like who is sponsoring the Outreachy interns for this community. A participation model has a "link" (a ForeignKey) to one `Community` and one `RoundPage` object. So, for example, we could say "Debian participated the May 2019 Outreachy internship round."

A project is represented by the `class Project` in `home/models.py`. It has a ForeignKey to a `Community`.

The relationships described above can be represented by this diagram:

![A Participation is related to a Community and a RoundPage. A Project is related to a Participation.](https://github.com/sagesharp/outreachy-django-wagtail/raw/master/docs/graphics/roundpage-community-participation-project.png)

# Adding a new Django app

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

# Dokku logs

If you've deployed to a test server with the Django debugging settings turned on, Django will send all emails to the console. If you want to create new test users, you'll need to extract the verification URL from the log. You can run:

```
ssh -t dokku@outreachy.org logs test
```

# Sentry error logging

Outreachy uses Sentry to log error messages received on both the Outreachy website and the test website. Unfortunately, that means if you ever use dokku to start the Python shell on the remote website, any typos you have end up getting reported to Sentry. To suppress those error messages, you can unset the `SENTRY_DSN` environment variable:

```
ssh -t dokku@www.outreachy.org run www env --unset=SENTRY_DSN python manage.py shell
```

# Rolling back migrations

If you have migrated the database (either locally or on the server) and want to go back to a previous migration, you can run:

```
./manage.py migrate home [version number]
```

# Delicate migrations

Sometimes a field doesn't work out exactly the way you wanted it to, and you want to change the field type. In this example, we'll be changing a simple BooleanField to CharField to support three different choices. This is a dance, because we want to preserve the values in the old field to populate the contents of a new field.

1. Define the new CharField. Set 'null=True' in the argument list.

2. Run `./manage.py makemigrations && ./manage.py migrate`

3. Create an empty migration: `./manage.py makemigrations home --empty`

4. Edit the new empty migration file. You'll need to define a new function that takes `apps` and `schema_editor`, like it's documented in the `0005_populate_uuid_values.py` file in the [Django "Writing a migration" documentation.](https://docs.djangoproject.com/en/1.11/howto/writing-migrations/). You can access the objects for that Model, and set the new field based on values in the old field. Make sure to add your function to the operations list. Note that you might have to copy some class members that represent the choice short code in the database into the migration, because all migrations only have access model class members that are Django fields (like CharField or BooleanField).

5. Remove the `null=True` argument from your model, and delete the old field. You might need to remove the field from admin.py and the views. Then run `./manage.py makemigrations && ./manage.py migrate`. That will generate a third migration to make sure the field must be non-null, but the second migration will set the field on all objects. When Django prompts you about changing a nullable field to a non-nullable field, choose 'Ignore for now'.

6. The third migration will fail if someone has added a new model object between the second migration and the third migration. In this case, you should roll back to the first migration (where you first added the field). You can pass the migration number to go back to: `./manage.py migrate home PREFIX` This should be a unique prefix (like the first four numbers of the migration). Then you can try to run the migration again: `./manage.py migrate`. Repeat as necessary.

# Why Django?

We evaluated a couple different choices:
 - CiviCRM
 - Wordpress
 - Red Hen
 - Django

CiviCRM proved too clunky to use, and ultimately their data model didn't necessarily fit our data models. Wordpress might have been fine with a template plugin and would have good user experience, but with everything we wanted to do, we felt we would ultimately outgrow Wordpress.

There are other proprietary tools for tracking sponsorship information, but since Outreachy is a project under the Software Freedom Conservancy and the Outreachy organizers believe in the power of free and open source, we have decided not to use proprietary software wherever possible.

Django fit our needs for flexibility, data model definition, and future use cases. However, the Django admin interface is pretty clunky and intimidating. We wanted to have a very easy way for all our organizers to quickly edit content. The Wagtail CMS plugin provides a nice user interface and template system, while still allowing programmers to fully use Django to implement models. It also provides internal revision tracking for page content, which means we can easily roll back content changes from the wagtail admin web interface if necessary.
