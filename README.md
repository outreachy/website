This repository is for the code that comprises the [Outreachy website](https://www.outreachy.org).

# What is Outreachy?

Outreachy provides remote internships. Outreachy supports diversity in open source and free software!

Outreachy internships are 3 months long. Interns are paid an internship stipend of $7,000 USD.

Interns work with experienced mentors from open source communities. Outreachy internship projects may include programming, user experience, documentation, illustration, graphical design,  data science, project marketing, user advocacy, or community event planning.

Outreachy internships are open to applicants around the world. Interns work remotely. Interns are not required to move.

We expressly invite women (both cis and trans), trans men, and genderqueer people to apply. We also expressly invite applications from residents and nationals of the United States of any gender who are Black/African American, Hispanic/Latinx, Native American/American Indian, Alaska Native, Native Hawaiian, or Pacific Islander.

Anyone who faces under-representation, systemic bias, or discrimination in the technology industry of their country is invited to apply.

# Outreachy-specific terms

Please use the gender-neutral ["they/them" pronouns](http://pronoun.is/they) and gender-neutral language to refer to all Outreachy participants.

The Outreachy community uses the following terms:

 * **FOSS:** Free and Open Source Software.
 * **Project:** A series of intern tasks to improve FOSS.
 * **Community:** A community is a set of related projects. For instance, if Django participated as an Outreachy community, the community might mentor projects to improve Django core functionality, Django extensions, or Django documentation.
 * **Mentor:** A mentor defines a project. They work with applicants to help them complete contributions to the project during the application process. A mentor selects an applicant to be the intern for their project. The mentor works remotely with the selected intern during the internship. An intern can have one or more mentors. Most Outreachy mentors only mentor one intern.
 * **Coordinator:** Each internship project must be associated with a FOSS community participating in Outreachy. That community provides funding for interns, either directly from community funds, or by finding a company or foundation to sponsor interns. Each community has one or more coordinators, who review submitted projects, approve mentors, set internship funding sources, and generally provide a communication link between the mentors and Outreachy organizers. Some smaller communities have only one coordinator, who is also the only mentor.
 * **Outreachy organizers:** There is a small set of organizers who oversee the entire Outreachy program. They communicate with coordinators about funding, onboard new communities, review intern feedback, authorize intern payments, answer questions, and promote the program to potential applicants.
 * **Applicant:** During the application process, Outreachy applicants make contributions to projects and apply to be an Outreachy intern.
 * **Intern:** An accepted applicant works with a mentor for three months during the internship period.

# Current state of Outreachy tech

The Outreachy web presence is in a couple of different places:
 * [Outreachy website](https://www.outreachy.org)
 * [GitHub website code repository](https://github.com/outreachy/website/)
 * [GitHub repository for creative works and miscellaneous scripts](https://github.com/outreachy/creative-works-and-scripts/)
 * [Repository CI Status](https://travis-ci.org/outreachy/website.svg?branch=master)

Older/deprecated websites include:
 - [GNOME Outreachy homepage](https://www.gnome.org/outreachy/) - shell homepage, where the outreachy.org domain currently redirects to
 - [GNOME wiki Outreachy pages](http://wiki.gnome.org/Outreachy) - moinmoin based wiki with information about how to apply and sponsor
 - [Outreachy application system](http://outreachy.gnome.org) - PHP-based application system currently hosted on OpenShift
 - irc.gnome.org #outreachy - Outreachy IRC channel - where applicants used to get help
 - [Outreachy Planeteria](http://www.planeteria.info/outreach) - blog aggregation for Outreachy interns

# Future Long-term Goals

 - Replace planetaria with one hosted on our domain (that allows for filtering which blogs are displayed?)
 - Track longitudinal information of alumni, so we can share success stories and improve our program
 - Track sponsorship information
 - Create a better way of displaying the list of potential Outreachy projects - e.g. allow searching, tagging for programming language or design or documentation or user experience

# Technology used in Outreachy website

## Commonly used technology

The Outreachy website is built with [Python](https://www.python.org/) and a web framework called [Django](https://www.djangoproject.com/). If you are creating new dynamic web content, you'll become familiar with Django over time.

Django allows us to build HTML using the [Django Templating Language](https://docs.djangoproject.com/en/3.1/topics/templates/). If you are editing static content, you will get familiar with the HTML templating language over time.

The Outreachy website uses the [Bootstrap](https://getbootstrap.com/docs/4.3/) framework for CSS and UI elements. If you are working with CSS, JavaScript, or HTML layout, you'll get familiar with Bootstrap over time.

## Less commonly used technology

There are a few pages that use [jQuery](https://learn.jquery.com/). You should not need to learn jQuery unless you're working on that code.

The Outreachy website uses a content management system called [Wagtail](https://wagtail.io/), which builds on top of Django. Wagtail is being depreciated from the Outreachy website, so you should not need to know much about it. What you do need to know is that Wagtail allows people to add static webpages and images to the Outreachy website.

Pages created and images uploaded to Wagtail do not become a part of this repository. Instead, the pages and images are stored on the website's remote database. So if you come across content that is not the git repository, it is probably stored in Wagtail on the Outreachy website server.

On the Outreachy webserver, we run [Dokku](http://dokku.viewdocs.io/dokku/). Dokku helps us deploy new code, manage our Let's Encrypt SSL certificates, and backup the Outreachy website database. Only Outreachy organizers have ssh access to push new code to the server. There should be no need for you to learn Dokku.

# Concepts and Resources

If you are going to be modifying the website's Python code, you may need to learn about some new topics. It's best to keep these resources on hand and reference them as needed, rather than reading them all the way through before starting on a task.

When modifying the Django Python code, the following resources can be helpful:

 * [Django documentation overview](https://docs.djangoproject.com/en/3.1/)
 * [Django tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial01/)
 * [Django topic guides](https://docs.djangoproject.com/en/3.1/topics/)
 * [Django models guide](https://docs.djangoproject.com/en/3.1/topics/db/models/)

## Database concepts

Unfortunately, the Django documentation assumes you already have some basic knowledge of database concepts. We wish it was more friendly to people who are new to databases. This section is an attempt to document additional resources you may want to read on database concepts. If you are still having trouble understanding Django documentation, please ask for help.

The Django documentation will talk about the "relationship" between two Django class objects.
 - [What is a database relationship?](https://database.guide/what-is-a-relationship/)

You will sometimes see fields of the type `ForeignKey`. Django has documentation on [foreign key fields](https://docs.djangoproject.com/en/3.1/ref/models/fields/#module-django.db.models.fields.related), but it assumes you know what a foreign key in a database is. If you are new to databases, we recommend reading about what a foreign key is:

 - [What is a primary key?](https://www.techopedia.com/definition/5547/primary-key)
 - [What is a foreign key?](https://www.techopedia.com/definition/7272/foreign-key)
 - [How do primary keys and foreign keys relate to each other?](https://database.guide/what-is-a-foreign-key/)

# Setting up your development environment

You can run Django locally to test changes to the code, test creating new pages, test adding new users, etc. The local tests you run will not impact the main Outreachy website, only your local version of the website. You should test changes locally before submitting a pull request.

To set up your local development environment, first clone the repository to your local machine:

```
git clone https://github.com/outreachy/website.git
```

In order to develop with Python, you'll need the Python 3 development headers, so install them. For example, on Debian or Ubuntu Linux, you can use `apt-get install python3-dev` to install the Python 3 development headers. On other Linux distributions, it may be called `python3-devel` or installed by default with `python` packages.

You'll also need to install node.js. If you're running Linux, it's recommended you install it using your package manager. If you're using Windows or Mac, follow the [installation instructions](https://nodejs.org/en/download/) on the node.js website.

Lastly, you need to check whether you have `libpq-dev` (also called `libpq-devel` or `postgresql-libs`) installed using your package manager. That package is necessary to build `psycopg2`, a PostgreSQL database adapter for Python, from source. If you're using Arch Linux, make sure you also have `base-devel` installed.

Next, you'll need to create a new virtualenv. A "virtualenv" is a separate virtual environment for working on different Python projects. It's good practice to create a virtual environment for each Python project you're working on, in case they have conflicting dependencies, and so that you make sure to record all the dependencies for each project.

These instructions will help you create a new virtualenv that will have all the python packages installed that you need to work on the Outreachy website. We use [pipenv](https://pipenv.readthedocs.io/en/latest/) for this purpose.

If you're using Linux, you may be able to install pipenv through your Linux package manager. On Debian or Ubuntu, you can run `sudo aptitude install pipenv`. Others distributions, like Arch Linux, may call it `python-pipenv`. Check [Pipenv's documentation on installing pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv) for more information.

The following command will automatically create a virtual environment and install the Python dependencies specified in the `Pipfile`. If you need help understanding pipenv, run `pipenv --help`.

Make sure that you have *not* run `pipenv shell` yet, then run these two commands:

```
cd website
pipenv install
```

If you accidentally ran `pipenv shell` before those two commands, you should exit the shell using CTRL+d. Then run the two commands.

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

and run the tests.

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py test
```

You'll need to set up a new internship round, following the instructions in the [Django shell section](#django-shell) and the [internship round section](#setting-up-a-new-internship-round).

# Misc virtual env topics

## Removing a virtual env

If you made a mistake in the directions above, you may need to remove your pipenv virtual environment. You can do that by running `pipenv --rm` in the website directory. If needed, you can delete the website directory and start over at the git clone command.

## Updating package dependencies

Sometimes you may want to add a new Django extension that uses additional Python packages. That means you'll need to record the new Python packages used. Pipenv automatically records changes in the project's dependencies in the `Pipfile` when you add/remove packages.

You can add a package with the command `pipenv install <package>`

You can remove a package with the command `pipenv uninstall <package>`

# Django shell

Django has a 'shell' mode where you can run snippets of Python code. You can exit the shell with CTRL+d at any time.

The Django shell takes a snapshot of the Python code base when you start the shell. If you change any of the website Python code, you'll need to exit the shell (CTRL+d) and restart it to reload the code.

You don't need to restart the shell if you're only making changes to HTML templates or CSS.

## Django shell usage cases

The Django shell is extremely useful for debugging the Python website code. You can run snippets of new code and examine variables as it runs. You can call into functions in the Outreachy website Python code.

The Django shell is also useful for testing code that accesses the underlying website database. You may be testing new Python code that query the database for objects that match your search. Sometimes it's hard to get the search parameters exactly right. You can use the Django shell to test complicated [query sets](https://docs.djangoproject.com/en/3.1/topics/db/queries/#retrieving-objects).

## Local vs remote Django shell

You can run the shell on either your local copy of the database, or you can run it on the remote server's database. If you start the shell on your local computer, it will load your local copy of the code and your local database. If you start the shell on the remote server, it will load the server's version of the code and the server's database.

# Setting up a new internship round

This section assumes you've cloned and [set up the Outreachy website development environment](#setting-up-your-development-environment).

## Django models vs database objects

The website Django code defines some object classes. These Python classes are abstractions of how Outreachy works. Think of classes as a template for defining a set of values.

For example, there is a Python class that represents all the data and dates that are associated with an Outreachy internship. The class includes dates for the application period, the contribution period, and the internship period. We call all the data associated with those dates an "internship round". The class that represents that set of dates is called "RoundPage" (for confusing historic reasons). You can find that class definition (and other classes) in `home/models.py`.

Each class in models.py defines an object in the underlying database. There is one "RoundPage" Python class that defines many internship round objects in the website database.

For example, we may have a series of dates associated with the May 2020 internship round. The internship might start on May 19, 2020 and end on August 18, 2020. The Python class RoundPage has a DateField internstarts that represents the internship start date. The RoundPage class also has a DateField internends that represents the internship end date.

The Django code uses these Python object classes to define the underlying database. When we create a database object for the May 2020 internship round, the Django code defines that the RoundPage object needs to have internship start and end dates. There may be other internship round objects in the database, such as objects for the May 2019 internship round, and the December 2019 internship round.

## Saving Django objects to the database

When you create a new object in the Django shell, you normally need to call the `save()` method to write the object to the local database. However, the following README sections use code in home/scenarios.py, and that code automatically calls the `save()` method for you. This can be confusing for newcomers to Django database concepts.

## Deleting database objects

Should you need to delete an object from the database, you can call the `delete()` method. Don't call `save()` after you call the `delete()` method, because that will write the object back to the database.

## Creating a new internship round in the database

When you first set up your development environment, your local website database will be empty. There will be no internship rounds in the database.

The website expects to have at least one past internship round. Some pages won't work without an internship round.

You'll need to create a new internship round database object. You can do that by using the Django shell.

```
./manage.py shell
```

You'll get a Python prompt that looks fairly similar to the standard Python shell, except that all the Django code you've written is available. It will look like this:

```
$ ./manage.py shell
Python 3.6.6 (default, Jun 27 2018, 14:44:17) 
[GCC 8.1.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> 
```

First, import all the models in `home/models.py`:

```
>>> from home import models
```

We'll also need to import all the methods in `home/scenarios.py`:

```
>>> from home import scenarios
```

The scenarios code creates database objects that represent the state of the website at particular times during the application, contribution, and internship periods. It automatically calculates the dates for internship round deadlines. It will also set up other database objects, such as mentors, coordinators, and project descriptions. The scenarios code is heavily used in the Outreachy tests (`home/tests_*.py`).

### Picking a scenario

Next, you'll want to pick *one* of the following scenarios to set up. Which scenario you pick depends on what task you're working on.

For example, if you were working on a task to add a new field to the initial application, you would want to run the "Scenario 3: Initial applications open" scenario code. If you were trying to fix a bug in the contribution recording form, you would want to run the "Scenario 4: Contributions open" scenario code.

Each scenario function in `home/scenarios.py` represents a different phase of the Outreachy internship round cycle:

 * [NewRoundScenario](#scenario-1-new-internship-round-dates) - Community CFP is first opened to ask for communities to sign up to participate as mentoring organizations
 * [CommunitySignupUnderwayScenario](#scenario-2-community-sign-up) - Mentors submit project descriptions
 * [InitialApplicationsUnderwayScenario](#scenario-3-initial-applications-open) - Initial applications are open for applicants to fill out
 * [ContributionsUnderwayScenario](#scenario-4-contributions-open) - Applicants with an approved initial application start to contribute to projects, project list is finalized
 * [ContributionsClosedScenario](#scenario-5-contributions-close) - The final application deadline has passed
 * [InternSelectionScenario](#scenario-6-intern-selection) - Mentors select their interns
 * [InternshipWeekScenario](#scenario-7-internship-week-n) - Internship phase, at various weeks in the 13 week internship

Once you've picked one scenario and run the code to update your local database, the next step is to [test the local website](#testing-the-local-website).

### Scenario accounts

Each scenario will create a series of accounts in your local website database.

All accounts created will have a default password of 'test'.

Account usernames will be automatically generated based on the type of account. For example, all applicants will have a username starting with 'applicant'. A number will be appended to the end of the username, e.g. applicant1, applicant2, applicant3, etc.

Here is a table of accounts you can log into, for each scenario:

| Scenario                            | coordinator1      | reviewer1 | mentor1 | applicant1 (to 8) | mentor2 (& 3) |
|-------------------------------------|-------------------|-----------|---------|-------------------|---------------|
| NewRoundScenario                    | x                 | x         |         |                   |               |
| CommunitySignupUnderwayScenario     | x                 | x         | x       |                   |               |
| InitialApplicationsUnderwayScenario | x                 | x         | x       | x                 |               |
| ContributionsUnderwayScenario       | x                 | x         | x       | x                 | x             |
| ContributionsClosedScenario         | x                 | x         | x       | x                 | x             |
| InternSelectionScenario             | x                 | x         | x       | x                 | x             |
| InternshipWeekScenario              | x                 | x         | x       | x                 | x             |

While the account username is standardized, the public name, legal name, and email address of the accounts are randomized. We use a library to generate random names. Unfortunately, the names it picks are typically white western-English names. Also, the randomly generated public name will often not match the email address at all. For example, Lydia Walsh may end up with an email address starting with marymclean. Finally, each account will have a set of pronouns chosen randomly.

Similarly, community names and project names are randomly generated words or phrases.

The following sections tell you how to use the Django shell to generate a scenario of the given type.

### Scenario 1: New internship round dates

The `NewRoundScenario` scenario represents the time when the Outreachy organizers first set dates for the new internship round. No communities have signed up to participate yet.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.

This scenario will also create the following database objects:
 - Internship round (`class RoundPage`) with dates and deadlines. The internship round will be created such that the date the community CFP opens (`RoundPage.pingnew`) is set to today.
 - Open source community (`class Community`). The community name will be randomly generated.

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:

```
>>> from home import scenarios
>>> scenario = scenarios.NewRoundScenario()
```

See the [Scenario accounts section](#scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 2: Community Sign-up

The `CommunitySignupUnderwayScenario` scenario represents the time when community coordinators are signing communities up to participate in Outreachy. One mentor has submitted their project.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentor (username 'mentor1')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - One project has been submitted (`class Project`) by mentor1 for this community. The project has been approved by the coordinator. The project title will be randomly generated.

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:

```
>>> from home import scenarios
>>> scenario = scenarios.CommunitySignupUnderwayScenario()
```

See the [Scenario accounts section](#scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 3: Initial applications open

The Outreachy application period has two distinct periods: the initial application period and the contribution period. During the initial application period, applicants submit an eligibility form and essays (an initial application).

The `InitialApplicationsUnderwayScenario` scenario represents the time during which applicants submit their initial applications.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentor (username 'mentor1')
 - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - One project has been submitted (`class Project`) by mentor1 for this community. The project has been approved by the coordinator. The project title will be randomly generated.
 - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
 - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
 - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
 - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
 - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:

```
>>> from home import scenarios
>>> scenario = scenarios.InitialApplicationsUnderwayScenario()
```

See the [Scenario accounts section](#scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 4: Contributions open

The Outreachy application period has two distinct periods: the initial application period and the contribution period. Applicants with an approved initial application will move onto the contribution period. Approved applicants will pick a project (or two), contact mentors, work on project tasks (contributions), and record those contributions in the Outreachy website.

The `ContributionsUnderwayScenario` scenario represents the time during which applicants communicate with mentors and work on project contributions.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentors (usernames 'mentor1' to 'mentor3')
 - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
 - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
 - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
 - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
 - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
 - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
 - A contribution (`class Contribution`) has been recorded by applicants applicant1 and applicant2
 - A final application (`class Contribution`) has been started by applicant1

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:
```
>>> from home import scenarios
>>> scenario = scenarios.ContributionsUnderwayScenario()
```

See the [test case scenario accounts section](#test-case-scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 5: Contributions close

The Outreachy application period has two distinct periods: the initial application period and the contribution period. Applicants with an approved initial application will move onto the contribution period. Approved applicants will pick a project (or two), contact mentors, work on project tasks (contributions), and record those contributions in the Outreachy website.

At the end of the contribution period, applicants fill out a final application. Most applicants who record a contribution will create a final application. The final application is due when the contribution period ends. Only applicants that have recorded a contribution and submitted a final application will be eligible to be selected as an intern.

The `ContributionsClosedScenario` scenario represents the time just after the contribution period closes.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentors (usernames 'mentor1' to 'mentor3')
 - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
 - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
 - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
 - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
 - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
 - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
 - A contribution (`class Contribution`) has been recorded by applicants applicant1, applicant2, applicant3, and applicant8
 - A final application (`class Contribution`) has been submitted by applicants applicant1, applicant2, applicant3, and applicant8

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:
```
>>> from home import scenarios
>>> scenario = scenarios.ContributionsClosedScenario()
```

See the [test case scenario accounts section](#test-case-scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 6: Intern selection

Once the contribution period ends, it is time for Outreachy mentors to select their interns. Coordinators will assign a funding source to each intern. Outreachy organizers will coordinate with mentors if there is an intern selection conflict between two projects. Outreachy organizers will review all interns and approve or reject them.

The `InternSelectionScenario` scenario represents the time just after the contribution period closes.

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentors (usernames 'mentor1' to 'mentor3')
 - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
 - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
 - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
 - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
 - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
 - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
 - A contribution (`class Contribution`) has been recorded by applicants applicant1, applicant2, applicant3, and applicant8
 - A final application (`class Contribution`) has been submitted by applicants applicant1, applicant2, applicant3, and applicant8
 - Interns have been selected (`class InternSelection`):
   - applicant1 has been selected as an intern to work with mentor1 (`class MentorRelationship`). The coordinator has not assigned a funding source for this internship. This internship is not yet approved by the Outreachy organizers.
   - applicant2 has been selected as an intern to work with mentor2 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
   - applicant3 has been selected as an intern to work with mentor3 (`class MentorRelationship`). The coordinator has requested that this internship be funded by the Outreachy general fund. This internship is not yet approved by the Outreachy organizers.

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:
```
>>> from home import scenarios
>>> scenario = scenarios.ContributionsClosedScenario()
```

See the [test case scenario accounts section](#test-case-scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

### Scenario 7: Internship week N

Each week during the internship, the Outreachy organizers have different tasks, emails to send, and intern chats to run.

The `InternshipWeekScenario` scenario will show you the website dashboard as it looks to the Outreachy organizers during each week of the internship.

Relevant dates are:
 - Week 1: internship starts
 - Week 2: internship chat, initial feedback due
 - Week 3: send blog post prompt email
 - Week 4: internship chat
 - Week 5: send blog post prompt email
 - Week 6: internship chat, midpoint feedback due
 - Week 7: send blog post prompt email
 - Week 8: internship chat
 - Week 9: send blog post prompt email
 - Week 10: internship chat
 - Week 11: send blog post prompt email
 - Week 12: internship chat
 - Week 13: send blog post prompt email
 - Week 14: internship chat (on last day), final feedback due

(These dates may vary from round-to-round.)

This scenario creates the following accounts:
 - Community coordinator account (username 'coordinator1'). The coordinator is approved as a coordinator for this community.
 - An initial application reviewer (username 'reviewer1'). The reviewer is approved to see initial applications.
 - Mentors (usernames 'mentor1' to 'mentor3')
 - Eight applicant accounts (usernames 'applicant1' to 'applicant8')

This scenario will also create the following database objects:
 - The community will be marked as being approved to participate in the current internship round (`class Participation`).
 - Information about which organization is sponsoring that community's interns this internship round (`class Sponsorship`).
 - Three projects has been submitted (`class Project`) by mentors mentor1, mentor2, and mentor3 for this community. The projects have been approved by the coordinator. The project titles will be randomly generated.
 - Initial application (`class ApplicantApproval`) for applicant1, applicant2, applicant3, and applicant8 have been approved
 - Initial application (`class ApplicantApproval`) for applicant4 is pending review by initial application reviewers
 - Initial application (`class ApplicantApproval`) for applicant5 has been rejected because they have too many full-time commitments during the internship period
 - Initial application (`class ApplicantApproval`) for applicant6 has been rejected for not aligning with Outreachy program goals
 - Initial application (`class ApplicantApproval`) for applicant7 has been rejected for not meeting Outreachy's eligibility rules
 - A contribution (`class Contribution`) has been recorded by applicants applicant1, applicant2, applicant3, and applicant8
 - A final application (`class Contribution`) has been submitted by applicants applicant1, applicant2, applicant3, and applicant8
 - Interns have been selected (`class InternSelection`):
   - applicant1 has been selected as an intern to work with mentor1 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
   - applicant2 has been selected as an intern to work with mentor2 (`class MentorRelationship`). The coordinator has said this internship will be funded by the community sponsors. This internship has been approved by the Outreachy organizers.
   - applicant3 has been selected as an intern to work with mentor3 (`class MentorRelationship`). The coordinator requested the internship be funded by the Outreachy general fund. However, the funding was denied, and the internship was not approved.

Which internship week you want depends on what part of the code you're working on. For example, if you wanted to see the changes you've made to the intern welcome email template, you would want to set the week to the first week.

To create this scenario in your local website database, start the Django shell. Then use the code in `home/scenarios.py` to generate the database objects:
```
>>> from home import scenarios
>>> scenario = scenarios.InternshipWeekScenario(week=1)
```

See the [test case scenario accounts section](#test-case-scenario-accounts) to understand what local website accounts are automatically created by this code.

Should any errors occur when running this code, follow the debugging techniques discussed in the [debugging scenarios code section](#debugging-scenarios-code).

If you pick the wrong scenario, or you want to start over with a new scenario, follow the instructions in the [create a different scenario section](#create-a-different-scenario).

## Create a different scenario

So, you picked a scenario and it turns out it wasn't the one you wanted. Or you ran some additional Django shell code, and now your website database is in a state you don't want.

Don't worry! You can start over with a fresh local database.

WARNING: the instructions in this section will delete your local database. You may want to save a copy of the database file with this command:

```
cp db.sqlite3 db.sqlite3.`date '+%Y-%m-%d-%H-%M'`
```

Now, we remove the local database:
```
rm db.sqlite3
```

To re-create the database, run the following commands:
```
./manage.py migrate
./manage.py createsuperuser
```

Last, [pick a new scenario](#picking-a-scenario) and run the code to create it.

# Debugging Tips

## Django shell help

The Django shell will print information about a class object. This includes the class methods and fields. This is a standard part of the Python shell, which Django shell builds on top of.

For example, assume you followed the instructions from one of the sections above to set up an internship round. You'll end up with a variable called `scenario`. That variable has a field called "round". `scenario.round` is an object of the RoundPage class. You can type the code below in the shell to look at the variables and fields in the RoundPage class:

```
>>> help(scenario.round)
Help on RoundPage in module home.models object:

class RoundPage(AugmentDeadlines, wagtail.wagtailcore.models.Page)
 |  RoundPage(*args, **kwargs)
 |  
```

You don't need have to have an object of the class type in order to ask for help. You can query the help for any model class. For example:

```
>>> from home import models
>>> help(models.RoundPage)
Help on RoundPage in module home.models object:

class RoundPage(AugmentDeadlines, wagtail.wagtailcore.models.Page)
 |  RoundPage(*args, **kwargs)
 |  
```

You can also use the help function to ask for help on Python built-ins. For example, you can ask for help about the date class in the Python datetime library:

```
>>> from datetime import date
>>> help(date)
```

## Debugging scenarios code

If you get an error when running the scenarios code, it's often hard to tell what exactly is wrong.

Most often, the issue is that you're creating an internship round twice. The RoundPage code uses the internship dates to create a unique "slug" for the RoundPage object. This "slug" is used in website URLs to reference that internship round. If you attempt to create an internship round twice, the slug will not be unique. The code will throw the error `django.core.exceptions.ValidationError: {'slug': ['This slug is already in use']}`.

Luckily, you can debug why the code is failing. You can do that by adding a with section to invoke the factories debugger, and an atomic transaction block. The atomic transaction block will ensure that no objects that were created before the factory method failed are saved to the database.

```
>>> from django.db import transaction
>>> import factory
>>> from home import scenarios
>>> with factory.debug(), transaction.atomic():
...     scenario = scenarios.InitialApplicationsUnderwayScenario()
>>>
```

(If you are running a different scenario code snippet than the one above, replace the indented line with the code that you were running that failed.)

The debugging output will be quite verbose, but you'll be able to see exactly which object creation call failed.

You can also look at all the objects in your database at once to see what a scenario created. From the shell you can quickly get all their short string representations for an overview:

```
>>> from django.apps import apps
>>> for model in apps.get_app_config('home').get_models():
...   print(model, model.objects.all())
```

Or, you can use Django's built-in `dumpdata` management command to get a JSON-formatted view of all fields in all the objects:

```
./manage.py dumpdata --indent 2 home
```


# Testing the local website

Once you've run the above setup commands, you should be all set to start testing your local website. First, run the command to start the Django webserver and serve up the local website.

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py runserver
```

To make sure you've set up an internship round successfully, go to the internship project selection page at `http://localhost:8000/apply/project-selection/`.

*Note: If you get an error saying "postcss: not found", make sure you run the whole command above, including the PATH part. For an explanation of what the PATH part of the command does, [read this issue comment](https://github.com/outreachy/website/issues/492#issuecomment-909371352).*

Once you go to `http://localhost:8000/apply/project-selection/`, you should see that the internship round dates are correct. If you created an internship round where the final application date has passed, you can see older rounds at `http://localhost:8000/past-projects/`.

To go to the Django administrative interface, go to `http://localhost:8000/django-admin/`. You can log in into with the account you created with `./manage.py createsuperuser`. If you're new to Django, you may want to find the RoundPage you created and edit some of the dates. You can find it by clicking the 'Round pages' link under the HOME section. You'll see the changed dates reflected in the internship project selection page if you refresh it.

It's unlikely you'll need to access the Wagtail admin interface, where the local CMS content is managed. If you do need to access the Wagtail admin interface, go to `http://localhost:8000/admin/`. Use the same account you created with the `./manage.py createsuperuser` command.

## Reloading the Django server

The runserver command takes a snapshot of the Python code base when you start it. If you change any of the website Python code, you'll need to exit the server (CTRL+c) and restart it to reload the code.

You don't need to restart the shell if you're only making changes to HTML templates or CSS.

# Tour of the code base

When you first clone this project, you'll see a couple top level directories:
 * `bin`
 * `contacts`
 * `docs`
 * `home`
 * `outreachyhome`
 * `search`

## Directory Structure

### Commonly used directories

If you are working on Python code, HTML templates, or adding static images, you'll spend most of your time in the `home` directory.

Key Python files and directories:
 * `home/models.py` - Python code that defines our custom Django database models
 * `home/views.py` - Python code that runs whenever you view a webpage or interact with a form
 * `home/urls.py` - parsing rules for translating URLs into which Python view code to call
 * `home/feeds.py` - when you add a blog post under home/templates/home/blog/ you'll need to manually add it to the RSS feed (which will automatically add it to the [blog index](https://www.outreachy.org/blog/)

Key HTML files and directories:
 * `home/templates/home/` - Most all of the important HTML templates are here
 * `home/templates/home/snippets` - small chunks of HTML that are included (embedded) in multiple templates
 * `home/templates/home/docs` - source files for the [Applicant Guide](https://www.outreachy.org/docs/applicant/) and the [Internship Guide](https://www.outreachy.org/docs/internship/)
 * `home/templates/home/email` - emails the website sends
 * `home/templates/home/blog` - blog post HTML (some posts are in the Wagtail CMS and are not in this git repository)
 * `home/templates/home/dashboard` - each Outreachy website account has a "dashboard" where important information, notices, and deadlines can be found

Key CSS files and directories:
 * `outreachyhome/templates/sass/` - CSS that overrides the default Bootstrap theme

### Less commonly used directories

The top-level directory `docs` is where our maintenance and design documents go. There is a work-in-progress guide for Outreachy organizer tasks. The `docs` directory also includes the intern and mentor agreements, and our privacy policy.

The `bin` directory almost never changes. It includes a script that's run by dokku before the website is deployed to outreachy.org.

The `outreachyhome` directory contains the base HTML page templates for all pages on the website. It also includes all the Django project settings for both development and production environments. This directory isn't changed very often.

### Directories not under revision control

If you've followed the steps above to set up your development environment, Django may have generated some directories and put files in them. Don't modify or commit files from those directories. You can use `git status --ignored` to show you which directories are not supposed to be under revision control. Top-level directories you shouldn't commit to are ones like `media`, `node_modules`, and `static`. These directories are in the .gitignore file, so your changes to those files won't be listed if you run `git status`.

## Working with HTML

Sometimes you'll want to edit the text on a web page. You know what the URL the text is found at, but you don't know which source file(s) it corresponds to.

There are a couple different ways to find the right html file to edit:

 * [Method 1: Django Debug Toolbar](#method-1-django-debug-toolbar)
 * [Method 2: Searching with git grep](#method-2-searching-with-git-grep)

### Method 1: Django Debug Toolbar

The Django Debug toolbar is the "DJDT" tab in the upper right corner of the page. It's only visible if you're running the website in debug mode, i.e. when you're using your local copy of the website.

For example, let's start the local webserver and navigate in a browser window to `http://localhost:8000/promote/`. Click the Django Debug Toolbar in the upper right corner of the page.

In this example, we want to know which HTML templates are used to create the promotion page. Click the "Templates" section of the toolbar.

A new page will pop up over the promotion page. It will show information about all the different HTML template pages that we used to create this page. The paths will be relative to the `home/templates/` directory. So the template path `home/promote.html` has an absolute path of `home/templates/home/promote.html`.

### Method 2: Searching with git grep

Find a less common phrase in the webpage. We recommend using part of a phrase, not a full sentence or paragraph. That's because the paragraph may be split across multiple lines, and the tools below stop looking for a match at the end of the line.

The best tool for searching is `git grep`. `git grep` only searches the files that are under revision control. It doesn't search generated files, or files you haven't committed yet. You can learn more about `git grep` by looking at its manual page:

`man git grep`
or
`git grep --help`

There are some pitfalls in this manual page. The `git grep` manual assumes you already some basic familiarity with the `grep` tool. So there are undocumented flags that you can pass to `grep` that `git grep` will also accept. However, `git grep` doesn't accept all the same flags that `grep` does. It's frustrating.

To understand what options you may be able to use with `git grep`, you may also need to read the `grep` manual page:

`man grep`
or
`grep --help`

**Simple examples:**

Search for the phrase "Outreachy Eligibility Rules":

`git grep "Outreachy Eligibility Rules"`

Show 10 lines before and 10 lines after the search phrase:

`git grep -B10 -A10 "Outreachy Eligibility Rules"`

**Complex examples:**

Search in the `home/templates/home` directory only:

`git grep "Outreachy Eligibility Rules" -- "home/templates/home"`

This command is a bit complex because it uses `grep` syntax to include the "pathspec" to search in. The pathspec strings must come after the "--" operator.

As of git 1.9.0, `git grep` allows you to exclude files and directories from showing up in your search matches. You can either use the ":(exclude)" or ":!" prefix to the exclude string.

To search for a number (like 49), excluding binary picture files, Python package lists, Django migration files, CSS, and JavaScript embedded into a specific HTML file:

```
git grep 49 -- ":(exclude)home/templates/home/stats_round_fifteen.html" ":(exclude)Pipfile.lock" ":(exclude)*.svg" ":(exclude)*.png" ":(exclude)*.ai" ":(exclude)*.eps" ":(exclude)*.jpg" ":(exclude)*.css" ":(exclude)home/migrations/*"
```

### Method 3: Following the Django trail

FIXME - Add instructions:
 - look in home/urls.py
 - find the view function in home/views.py
 - see which template it uses
   - sometimes it doesn't show a template - but one with a similar name is automatically used
 - use the templates includes to see what other templates are included in this one

## Template includes

Move the text from the section "3. Identify which templates are included in the template under test." here.
Link to this section in that section.

# Django apps

## Outreachy Django apps

Django breaks up functionality into a project (a Django web application) and apps (smaller a set of Python code that implements a specific feature). There is only one project deployed on a site at a time, but there could be many apps deployed. You can read more about what an application is in [the Django documentation](https://docs.djangoproject.com/en/2.0/ref/applications/).  

In the Outreachy repository, the directory `outreachy-home` is the project. We have several apps:
* `home` which contains models used on most the Outreachy pages
* `search` which was set up during the wagtail installation to allow searching for pages and media
* `contacts` which is a Django app for our contact page

## External Django Packages

The Outreachy website also uses some Django apps that are listed in the `INSTALLED_APPS` variable in `outreachyhome/settings/base.py`. The Python module code for those Django apps aren't found in top-level directories in the repository. That's because the Python module code was installed into your virtualenv directory when you ran `pipenv install`. That command looked at the Python package requirements listed in `Pipfile` and installed each of the packages.

If you want to look at the source code of the installed external Django applications, you can use `pipenv open MODULE` to examine the source code files associated with that module. For example, say you notice the `home/models.py` file has an import line `from django.contrib.auth.models import User`. You can use pipenv open to look at the models.py file that contains the User class by running the command `pipenv open django.contrib.auth`. That will open all the files in the auth module in your editor, and you can then open models.py and search for `class User`.

# Outreachy website models

Django defines "models" which are templates to store data in the database. Most of the Outreachy website models can be found in `home/models.py`.

The models in this code reflect the organization of Outreachy. That means in order to work on the code, you may need to understand how our internship program works: the application and internship cycle, volunteer roles, and a little bit about how our internships are funded.

It can seem daunting to look at many models! Please ask for help when you're stuck or confused about the models. It's likely confusing because our organization has grown organically over the last 10 years, and our code base reflects that.

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

## Internship Rounds and Communities

The Outreachy internship round is represented by `class RoundPage` in `home/models.py`. It contains dates that define the phases of the internship rounds, the round name, the round number, links to future intern chats over video and text.

A FOSS community is represented by the `class Community` in `home/models.py`. It contains things like the community name.

Communities can participate in multiple Outreachy internship rounds. We record their participation in each round in with the `class Participation` in `home/models.py`. A participation includes details like who is sponsoring the Outreachy interns for this community. A participation model has a "link" (a ForeignKey) to one `Community` and one `RoundPage` object. So, for example, we could say "Debian participated the May 2019 Outreachy internship round."

The relationships described above can be represented by this diagram:

![A Participation is related to a Community and a RoundPage. A Project is related to a Participation.](https://github.com/outreachy/website/raw/master/docs/graphics/RoundPage-Community-Participation-Project.png)

## ApprovalStatus class

You'll notice in the diagram above that both `class Participation` and `class Project` have `class ApprovalStatus` as a base class. The ApprovalStatus class is a way to keep track of who submitted an object, who has permissions to approve an object, and what the status of the approval is. An ApprovalStatus object can be in the pending, approved, rejected, or withdrawn state.

Outreachy coordinators sign up their community to participate in a particular Outreachy internship round. That puts the associated Participation into the pending state. Outreachy organizers then review the Participation and approve or reject it. Coordinators can withdraw their community's participation at any time. For Participation objects, coordinators are considered the submitters of the Participation, and organizers are the approvers.

Once a community signs up to participate (and even before it's approved), Outreachy mentors can submit projects. That puts the associated Project into the pending state. Coordinators then review the Project and approve or reject it. Project mentors can withdraw their project's participation at any time. For Project objects, mentors are the submitters and coordinators are the approvers.

Most classes with an ApprovalStatus will have emails sent to the submitter when they are approved, but some don't. Review the view code in `home/views.py` to see what emails are sent when the status changes.

## CoordinatorApproval class

The community coordinator role is represented by the CoordinatorApproval class. It has a foreign key to a Community, because we expect the coordinator to remain the same from round to round. New coordinators are on-boarded as people change roles, but most coordinators stick around for at least 2-4 internship rounds.

![A CoordinatorApproval has a foreign key to a Community.](https://github.com/outreachy/website/raw/master/docs/graphics/Participation-Community-CoordinatorApproval-Project-MentorApproval.highlighted-CoordinatorApproval.png)

When testing the website on your local machine, it's useful to create a coordinator account that you can log into. This allows you to see how the website looks at various points in the round to a coordinator. You can create a new CoordinatorApproval object using the `home/factories.py` function `CoordinatorApprovalFactory()`.

The factory will fill in random names, phrases, and choices for any required fields in the CoordinatorApproval, Comrade, User, and Community objects. If you want to override any of those fields, you can pass that field value as an assignment in the same format you would for a [Django filter queryset](https://docs.djangoproject.com/en/3.1/topics/db/queries/#retrieving-specific-objects-with-filters).

In the example code below, we'll create a new CoordinatorApproval object. The factories code automatically sets all passwords for User accounts to `test`. We'll set the CoordinatorApproval approval status to approved (by default, all ApprovalStatus objects are created with the withdrawn approval status). The example sets the community name to "Really Awesome Community", but you can use the name of your favorite FOSS community instead.

```
>>> name = "Really Awesome Community"
>>> coord1 = CoordinatorApprovalFactory(
	coordinator__account__username="coord1",
	approval_status=ApprovalStatus.APPROVED,
	community__name=name,
	community__slug=slugify(name))
>>> really_awesome_community = coord1.community
```

If you want to create a second coordinator under the same community, you can run this command:

```
>>> coord2 = CoordinatorApprovalFactory(
	coordinator__account__username="coord2",
	approval_status=ApprovalStatus.APPROVED,
	community=really_awesome_community)
```

If you visit `http://localhost:8000/communities/cfp/really-awesome-community/`, you should see the randomly generated names of the coordinators. You can log in with the superuser account or one of the coordinator's accounts to see how the page changes once you log in.

## Participation and Sponsorship classes

Each community can sign up to participate in an Outreachy internship round. That sign up is represented by `class Participation`. As part of signing up to participate in Outreachy, each community must provide sponsorship for at least one intern ($6,500 USD). When a community signs up, we require the coordinator to fill out information about their sponsor names and sponsorship amounts. The sponsor information is stored in `class Sponsorship`, which has a foreign key to the Participation object.

You can use the Django shell to create a new participation. The example below assumes you already have a pre-created community that is being referenced by the variable name `really_awesome_community`, and a pre-created RoundPage stored in the variable `scenario.round`. The code also sets the approval status to say the community has been approved to participate in this round. The example sets that the community will be receiving sponsorship for two interns. We'll save a reference to that Participation object in the variable participation.

```
>>> sponsorship = SponsorshipFactory(
	participation__participating_round=scenario.round,
	participation__community=really_awesome_community,
	participation__approval_status=ApprovalStatus.APPROVED,
	amount=13000)
>>> participation = sponsorship.participation
```

## Project and MentorApproval classes

In Outreachy, mentors submit projects under a participating community. Mentors are in charge of defining the project description and tasks that the applicants work on during the contribution phase. Each project can have one or more mentors.

A project is represented by the `class Project` in `home/models.py`. It has a ForeignKey to a `Participation` (the representation of a community participating in an internship round).

The mentor(s) for that project are represented by the `class MentorApproval` in `home/models.py`. That provides a link between the mentor's account on Outreachy (a `Comrade` object) and the Project object. A mentor submit or co-mentor more than one project, which will create multiple MentorApproval objects.

![A MentorApproval has a foreign key to a Project.](https://github.com/outreachy/website/raw/master/docs/graphics/Participation-Community-CoordinatorApproval-Project-MentorApproval.highlighted-MentorApproval-Project.png)

When testing the website on your local machine, it's useful to create a mentor account that you can log into. This allows you to see how the website looks at various points in the round to a mentor. You can create a new MentorApproval object using the `home/factories.py` function `MentorApprovalFactory()`.

The factory will fill in random names, phrases, and choices for any required fields in the Comrade, User, and Project objects. If you want to override any of those fields, you can pass that field value as an assignment in the same format you would for a [Django filter queryset](https://docs.djangoproject.com/en/3.1/topics/db/queries/#retrieving-specific-objects-with-filters).

In the example Django shell code below, we'll create a MentorApproval object. The factories code automatically sets the password for the mentor to `test`. We'll set the MentorApproval approval status and the Project approval status to approved. (By default, all ApprovalStatus objects are created with the withdrawn approval status.) The code assumes you have a pre-created Participation object referenced by the variable `participation`. The code will associate the Project with that community's participation in the internship round, rather than allowing the factories code to create new Community and RoundPage objects with random values.

```
>>> mentor1 = MentorApprovalFactory(
	mentor__account__username="mentor1",
	approval_status=ApprovalStatus.APPROVED,
	project__project_round=participation,
	project__approval_status=ApprovalStatus.APPROVED)
>>> project = mentor1.project
```

If you want to create a co-mentor under the same project, you can run these two commands:

```
>>> mentor2 = MentorApprovalFactory(
	mentor__account__username="mentor2",
	approval_status=ApprovalStatus.APPROVED,
	project=project)
```

## Models for Applicants

When a person wants to apply to Outreachy, their first step is to fill out an initial application. That application is reviewed by Outreachy organizers and approved or rejected. The initial application may be automatically rejected if the person is not eligible to be paid or they have too many time commitments. The initial application must be re-submitted each internship round, because the person's time commitments and payment eligibility may change from round to round. The initial application is represented by `class ApplicantApproval`.

After the applicant's initial application is approved, their next step is to pick one or more Outreachy projects and make a contribution to it. A contribution is a small task that an applicant finds in the project's issue tracker. Once a contribution is started, the applicant can then record the contribution in the Outreachy website. The contribution form asks for the date started, completed, a URL for the contribution (typically to the issue tracker), and a description of the contribution. The recorded contribution is represented by `class Contribution`.

The last step is for an applicant to create a final application to each project they made a contribution to. The final application includes questions about the applicant's past experiences with FOSS communities, relevant projects, and a timeline of project tasks for the internship project they're applying to. The final application is represented by `class FinalApplication`.

Applicants can record many contributions for the same Project, or different projects. Applicants can submit multiple final applications to different projects. The associated Contribution and FinalApplication objects will all have foriegn keys back to the ApplicantApproval and Project objects.

If the applicant applies to another round, they have to create a new initial application (ApplicantApproval object) and new Contribution and FinalApplication objects associated with the Project they're applying for.

![Diagram showing the relationship from a RoundPage through a Project to a Contribution, then an ApplicationApproval, to a FinalApplication](https://github.com/outreachy/website/raw/master/docs/graphics/RoundPage-Participation-Project-Contribution-ApplicantApproval-FinalApplication.png)

### Creating ApplicantApproval Test Objects

It can be useful to log into your local test website and see how the pages look from an applicant's perspective. The following Django shell example creates a new ApplicantApproval. It assumes you already have a pre-created RoundPage referenced by the variable `scenario.round`. It sets the initial application's approval status to approved. The code sets the applicant's account username. The factories code automatically sets the password to `test`.

```
>>> applicant1 = ApplicantApprovalFactory(
	application_round=scenario.round,
	approval_status=ApprovalStatus.APPROVED,
	applicant__account__username="applicant1")
```

### Creating Contribution Test Objects

The following Django shell example creates a new Contribution object. It assumes you already have a pre-created ApplicantApproval referenced by the variable `applicant1` and a pre-created Project referenced by the variable `project`.

```
>>> ContributionFactory(
	project=project,
	applicant=applicant1,
	round=project.project_round.participating_round)
```

### Creating FinalApplication Test Objects

The following Django shell example creates a new FinalApplication object. It assumes you already have a pre-created ApplicantApproval referenced by the variable `applicant1` and a pre-created Project referenced by the variable `project`. It sets the FinalApplication approval status to pending.

```
>>> FinalApplicationFactory(
	project=project,
	applicant=applicant1,
	round=project.project_round.participating_round,
	approval_status=ApprovalStatus.PENDING)
```

## InternSelection and MentorRelationship classes

When the contribution period is over and the deadline has passed to submit a final application, Outreachy mentors decide which interns they want to select. As part of that process, they must sign a mentor agreement that states they understand their commitments to this internship. The signed contract for this internship with this applicant is stored in `class MentorRelationship`.

When the mentor picks an intern, that intern selection is represented by `class InternSelection`. That model stores information about the internship, such as what project the applicant will be interning with, if the intern has custom start or end dates, if the internship is approved by the Outreachy organizers, etc.

If a co-mentor for the same Project signs up to participate as a mentor for this intern, another MentorRelationship object will be created. Mentors from a different Project can select the applicant as an intern. That would create a MentorRelationship to the MentorApproval for that mentor in that other project. If mentors from two different projects select the same applicant, it shows up as an intern selection conflict on their project applicant review page, the community applicant review page, and the organizer dashboard.

The relationship between an InternSelection and a MentorRelationship is shown below:

![An InternSelection is related to a MentorApproval through a MentorRelationship](https://github.com/outreachy/website/raw/master/docs/graphics/MentorApproval-MentorRelationship-Project-ApplicantApproval-InternSelection.png)



# Invalid HTML and testing

When you're testing a view, you may want to test that certain HTML elements are present.
You can do this by passing `html=True` to `AssertContains` or `AssertNotContains`.

However, that function will throw an error if the HTML is invalid.
This could be something as small as forgetting a div or paragraph tag.
Finding the mistake can be difficult, especially if the Django template
[includes other template files](https://docs.djangoproject.com/en/3.1/ref/templates/builtins/#include).

Additionally, the templates rendered in the test may not be the same as
manually re-creating the test case in your local copy.

So, here is a way to find out what HTML is invalid, in which template file:

1. In the test function, write out the HTML contents to a file:

```
        with open("/tmp/response.html", "wb") as f:
            f.write(response.content)
```

2. Use xmllint to find HTML errors in the file:

```
xmllint --format --html /tmp/response.html > /dev/null
```

3. Identify which templates are included in the template under test.

For example, say we're testing the file `home/templates/home/applicant_review_detail.html`.
We want to know what templates that file includes, and what templates those files include, etc., until we know the full tree of includes.

There is a custom management command that finds all the other templates
that are included in Django template file.
You have to pass in the template name as you would do with an `include` tag.
That means you have to strip off the `home/templates/` prefix.

So we run the following command to see all included templates in a file:

```
./manage.py template_includes home/applicant_review_detail.html
```

That will give you the following list:

```
home/applicant_review_detail.html
  home/snippet/application_review_headers.html
  home/snippet/application_review_rows.html
    home/snippet/essay_rating.html
    home/snippet/red_flags_display.html
  home/snippet/applicant_review_actions.html
    home/snippet/applicant_essay_rating_form.html
  home/snippet/time_commitment_overview.html
  home/snippet/applicant_review_time_commitments.html
  home/snippet/applicant_location.html
  home/snippet/applicant_review_essay_rating.html
```

4. Then you'll want to run each snippet through xmllint to find HTML validation errors.
This will print the actual lines in the file that needs to be corrected.

```
xmllint --format --html home/templates/home/snippet/file.html > /dev/null
```

You may need to correct several HTML validation errors.

# Running tests manually

## Starting tests manually

If you want to run the test suite manually, you can run the command:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py test home/
```

You can add verbosity flags to get more output from the tests:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py test -v2 home/
```

You can run tests from a particular file by passing the file name without the .py extension:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py test home.<file name>
```

You can run one test in a particular file:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py test home.<file name>.<class name>.<function name>
```

## Running test code in the shell

Sometimes when writing a new test, you want to test your code in the shell first. The test suite will do some set up automatically to create a local test Client that uses your local code and a new test database. You can replicate that by running the following commands:

```
PATH="$PWD/node_modules/.bin:$PATH" ./manage.py shell
Python 3.6.8 (default, Jan  3 2019, 03:42:36) 
[GCC 8.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from django.test import Client
>>> c = Client(HTTP_HOST='localhost')
```

Now you can create objects and look at responses from page requests against your local database, e.g.:

```
>>> from django.urls import reverse
>>> from home.scenarios import *
>>> InternshipWeekScenario(week = 1, community__name='Debian', community__slug='debian')
<home.scenarios.Scenario object at 0x7f5797f6c438>
>>> response = c.get('/communities/cfp/debian')
>>> response.status_code
200
```

Sometimes the page contains a form and the form has validation errors.
That usually shows up as a '200' (OK) response code, rather than a '302' (Redirect) response code.

You can access those form validation errors from the shell or within a test.
The trick is that the response is not just an [HttpsResponse](https://docs.djangoproject.com/en/3.1/ref/request-response/#httpresponse-objects) class object, it's a [TemplateResponse](https://docs.djangoproject.com/en/3.1/ref/template-response/) class object.
You can access the form through the TemplateResponse context dictionary. Then you can print any [form validation errors](https://docs.djangoproject.com/en/3.1/ref/forms/validation/):

```
>> print(response.context['form'].errors)
```

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

# Migrations

When you change some aspect of a field in a model, that can create a change to the underlying database information. For example, if you change a field name from "foo" to "bar", the Django object database has to change such that you can quenry for objects using the new name. You can read more about migrations and how to create and apply them in the Django migrations documentation. We suggest starting with the [simple migrations introduction in the Django tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial02/#activating-models), and then looking at the [more detailed migrations documentation](https://docs.djangoproject.com/en/3.1/topics/migrations/) if needed.

In most cases, there are only two commands you need to run to create and apply a migration. The first is:

```./manage.py makemigrations```

This will examine the code changes you've made, and automatically generate a Python file that describes how the underlying database schema should change. Make sure to commit this file along with your model code changes. Then the second command you'll run is:

```./manage.py migrate```

This will apply the database schema change to your local test environment. If the Outreachy organizers push a change that includes a migration to the production or testing sites, they will need to update the server's database schema by running `ssh dokku@outreachy.org run www python manage.py migrate` or `ssh dokku@outreachy.org run test python manage.py migrate`.

The next two sections describe some of the trickier aspects of migrations that we've run into.

## Rolling back migrations

If you have migrated the database (either locally or on the server) and want to go back to a previous migration, you can run:

```
./manage.py migrate home [version number]
```

## Delicate migrations

Sometimes a field doesn't work out exactly the way you wanted it to, and you want to change the field type. In this example, we'll be changing a simple BooleanField to CharField to support three different choices. This is a dance, because we want to preserve the values in the old field to populate the contents of a new field.

1. Define the new CharField. Set 'null=True' in the argument list.

2. Run `./manage.py makemigrations && ./manage.py migrate`

3. Create an empty migration: `./manage.py makemigrations home --empty`

4. Edit the new empty migration file. You'll need to define a new function that takes `apps` and `schema_editor`, like it's documented in the `0005_populate_uuid_values.py` file in the [Django "Writing a migration" documentation.](https://docs.djangoproject.com/en/3.1/howto/writing-migrations/). You can access the objects for that Model, and set the new field based on values in the old field. Make sure to add your function to the operations list. Note that you might have to copy some class members that represent the choice short code in the database into the migration, because all migrations only have access model class members that are Django fields (like CharField or BooleanField). For an example, see the `home/migrations/0068_auto_20180828_1832.py` file in this repo.

5. Remove the `null=True` argument from your model, and delete the old field. You might need to remove the field from admin.py and the views. Then run `./manage.py makemigrations && ./manage.py migrate`. That will generate a third migration to make sure the field must be non-null, but the second migration will set the field on all objects. When Django prompts you about changing a nullable field to a non-nullable field, choose 'Ignore for now'.

6. The third migration will fail if someone has added a new model object between the second migration and the third migration. In this case, you should roll back to the first migration (where you first added the field). You can pass the migration number to go back to: `./manage.py migrate home PREFIX` This should be a unique prefix (like the first four numbers of the migration). Then you can try to run the migration again: `./manage.py migrate`. Repeat as necessary.

## Deleting old migrations

Each time the Django models change, Django creates a [migration file](https://docs.djangoproject.com/en/4.1/topics/migrations/). Everytime you need to run tests, Django creates a new test database, and applies all migrations. That means that if you have many migrations, starting a test can take a long time, because all the migrations need to be applied.

A way to work around this is to either:
 1. Squash migrations periodically
 2. Delete all migration files and recreate one new migration file

Squashing migrations only works if you don't have a RunPython command in any migration file. We often use that command to deal with tricky migrations, such as moving old data from one field to a new field.

If you can, please use squash migrations. Otherwise, read on for the second option.

Delete all migration files and recreate one new migration file by:

Check out a new branch:

```git checkout -b delete-old-migrations```

Delete the migration files from both git's history and the migration directory for the home app:

```git rm home/migrations/0*```

(I wasn't sure whether to leave the empty __init__.py file, so I deleted all migration files that started with 0. If you have over 1,000 migration files, you'll need to also delete files starting with 1.)

Then run the command to make one new migration file, based on the current home/models.py file:

```./manage.py makemigrations```

Copy the production database twice -- once as a backup, in case production migration fails, and the second time as a test database update:

```
ssh dokku@outreachy.org postgres:clone www-database test-database-updated-2022-12-26
ssh dokku@outreachy.org postgres:clone www-database www-database-backup-2022-12-26
```

Link the copied production database into the test server:

```
ssh dokku@outreachy.org postgres:link test-database-updated-2022-12-26 test
```

Unlink the old test database from the test server:

```
ssh dokku@outreachy.org postgres:unlink test-database-updated-2022-11-21 test
```

Edit the app.json file in the top-level directory of the code repo. You will change the line that auto-migrates on a git push to instead migrate with the --fake-initial flag.

Make sure to commit the app.json file in the same commit that removes the old migration files and adds the new clean migration file.

```
git add app.json
```

TLDR; the --fake-initial flag lets us create one new migration file to represent all our migrations, and not touch the production or test database tables.

Details: This special flag is needed because there is a mismatch in expectations between what the newly created migration file expects and the actual state of the production or test database.

The newly created migration code assumes that the database it starts with is fresh and empty, with no database tables. It wants to write thos new database tables to the empty database.

However, our production and test servers already have those database tables in them. Moreover, it already contains a lot of data! We don't want to delete that data, or those database tables. The tricky part is that internally, Django keeps track of which migrations are applied to the database. So we have to do something special to update Django's migration tracking database.

The --fake-initial flag will tell Django, "Hey, the database schema already matches this migration I'm asking you to apply, so pretend you applied it and don't actually run the code to migrate." The flag will ask Django to delete the table in its migration tracking database, and then mark the new, one-file migration as applied without actually running the migration code.

The final result is that Django will assume our new one-file migration has been applied. In the future, when we modify the models, Django will apply that new migration on top of the one-file migration.

Push the new code to the test server, which will apply the app.json file, and should fake migrate the database.

```
git push dokku-test delete-old-migrations:master
```

Pushing to the dokku test webserver git repo will result in the Outreachy test being rebuilt. During the rebuild process, you will see a line saying that the --fake-initial flag is being used:

```
-----> Releasing test...
-----> Checking for predeploy task
-----> Executing predeploy task from app.json: python manage.py migrate --fake-initial
=====> Start of test predeploy task (ed8c12901) output
       Operations to perform:
         Apply all migrations: admin, auth, contenttypes, home, reversion, sessions, taggit, wagtailadmin, wagtailcore, wagtaildocs, wagtailembeds, wagtailforms, wagtailimages, wagtailredirects, wagtailsearch, wagtailusers
       Running migrations:
         No migrations to apply.
=====> End of test predeploy task (ed8c12901) output
```

Double check things are working on the test server. Go to your account page, and change your avatar. After saving, re-open the account page and make sure the new picture is displayed. Edit a model through the Django web interface and make sure the changes show up on pages that display its fields. Etc.

Update the app.json file to use the --noinput flag instead of the --fake-initial flag. Then add the file to git and commit it:

```
git add app.json
git commit -m "Revert app.json file to migrate automatically on git push to the webserver repo"
```

Push the changed app.json file to the test server:

```
git push dokku-test delete-old-migrations:master
```

Pushing to the dokku test webserver git repo will result in the Outreachy test being rebuilt. During the rebuild process, you will see a line saying that the --noinput flag is being used:

```
-----> Releasing test...
-----> Checking for predeploy task
-----> Executing predeploy task from app.json: python manage.py migrate --noinput
=====> Start of test predeploy task (ecfd4fbd7) output
       Operations to perform:
         Apply all migrations: admin, auth, contenttypes, home, reversion, sessions, taggit, wagtailadmin, wagtailcore, wagtaildocs, wagtailembeds, wagtailforms, wagtailimages, wagtailredirects, wagtailsearch, wagtailusers
       Running migrations:
         No migrations to apply.
=====> End of test predeploy task (ecfd4fbd7) output
```

Double check that the test website still works again.

Next, change a model, create a new migration, and push those changes to the test webserver's git repo.

You should see output similar to the following:

```
-----> Releasing test...
-----> Checking for predeploy task
-----> Executing predeploy task from app.json: python manage.py migrate --noinput
=====> Start of test predeploy task (c10a5d3b0) output
       Operations to perform:
         Apply all migrations: admin, auth, contenttypes, home, reversion, sessions, taggit, wagtailadmin, wagtailcore, wagtaildocs, wagtailembeds, wagtailforms, wagtailimages, wagtailredirects, wagtailsearch, wagtailusers
       Running migrations:
         Applying home.0002_auto_20221226_2301... OK
=====> End of test predeploy task (c10a5d3b0) output
```

Now that we've made sure the test webserver works, it's time to apply a similar process to the production webserver.

First, we need to push the commit that deleted all the old migration files, and disabled automatic migrations.  We can find which commit we need by running:

```
git log --pretty=oneline --abbrev-commit
```

Let's say that gave us the following output:

```
4a6a57bc (HEAD -> 2022-12-delete-old-migrations, dokku-test/master) Revert "Add Outreachy longitudinal survey"
a2264fa8 README: Document how to carefully start with a new set of migration files.
097beb12 Revert app.json file to migrate automatically on git push to the webserver repo
5057a2aa Replace migration files with one new migration.
c4bac9b9 (github/master, dokku/master, master) Replace image on thank-you post, and center image
```

Find the commit hash for when we removed the old migration files. It should be the first commit on top of the dokku/master HEAD commit. In the above case, the commit is `5057a2aa`.

Now, push that commit to the production server's master branch:

```
git push --no-verify dokku 5057a2aa:master
```

You should see output showing that the `--fake-initial` flag is being used.

Next, push the commit to revert the app.json file to the production server's master branch:

```
git push --no-verify dokku 097beb12:master
```

You should see output showing that the `--noinput` flag is being used, and that there are no migrations to apply.

Next, try pushing the commit that edited some models:

```
git push --no-verify dokku 4a6a57bc:master
```

You should see log output that shows the new migration was applied to the production database.

Double check things are working on the production server. Check that any model changes are showing up in the Django admin interface.

Once you are *absolutely positively sure* that the changes haven't caused any issues, you should delete the backup www database using the `postgres unlink` and `postgres destroy` dokku commands.

# Testing locally with production database

If you are one of the few people with access to the Outreachy production webserver, you can run a copy of the production database in your local development environment. Do this with extreme care on an updated, secure system with full-disk encryption.

First, export the production website postgres database to a local file on your computer:

```
ssh dokku@outreachy.org postgres:export www-database-updated > outreachy-website-database-backup-DATE.sql
```

Next, install postgres using your Linux distribution package manager, or other operating system installation instructions. You will need postgres 16 or later.

Installing postgres should also create a new postgres cluster for you. We'll use that default created cluster to add the Outreachy website database to.

Login as the postgres user:

```
sudo -i -u postgres
```

In this new shell, create a database user with the same name as your local computer's login name:

```
createuser --interactive -DRS --pwprompt
```

Pick a new password that is different from your computer's account password. This password will need to be passed on the shell prompt, so it will be stored in the shell command history in .bash_history. Therefore using your laptop's account password is not advised.

Next, create a database that your user has access to:

```
createdb -O LOGIN_NAME www_database
```

Log out of the postgres user (typically you do this by pressing CTLR+d).

Now as your normal user, import the exported production database to your newly created local database:

```
pg_restore --verbose --clean -d www_database outreachy-website-database-backup-DATE.sql
```

Find out which port postgres is running on. This command will list the port number in the third column:

```
pg_lsclusters
```

Now you can start a local website server that will read and write to your newly imported database. Replace the following variables with ones used or found in the previous commands: `LOGIN_NAME`, `PASSWORD`, and `PORT`.

```
PATH="$PWD/node_modules/.bin:$PATH" DATABASE_URL=postgresql:///LOGIN_NAME:'PASSWORD'@locahost:PORT/www_database ./manage.py runserver
```

That will start the local Django web server.

Now you can log in to localhost using your account username and password from the production server.

# Updating the Outreachy web server

Before updating the web server, make a back-up image. Also export the postgres www database to somewhere safe.

Make sure to read the [dokku updating instructions](https://dokku.com/docs/getting-started/upgrading/) *before* you update Debian. Updating Debian will install a new version of dokku. That may mean you need to take extra steps after the Debian update.

The Outreachy website Linux server should be running the latest [Debian stable release](https://wiki.debian.org/DebianStable). Read the [Debian releases page](https://wiki.debian.org/DebianReleases) to understand what Debian stable means. For now, consider 'stable' to be a Debian release that's tagged as the latest stable version.

Check which Debian version is considered the current stable release. If the server is running 'oldstable' or older, it's time to upgrade. Otherwise, stick with the server running a stable release rather than a testing release. As the Debian wiki notes, "Only stable is recommended for production use."

Read the paragraphs below, and then follow the [instructions for upgrading Debian](https://wiki.debian.org/DebianUpgrade) to the latest stable release.

A Debian release is made up of different software versions, bundled into software 'packages'. You will update the Debian release by editing 'apt' files. These files tell the package manager which Debian release to fetch software packages from.

You'll want to use the code name for the release (e.g. bookworm or trixie) in your apt files, rather than the release tag 'stable'. That's because which Debian version is tagged as 'stable' changes immediately when a new Debian release comes out. If you use a code name, your software packages will always come from that release. If you use the stable name in your apt sources, you be forced to use software packages from the newly released stable version as soon as it comes out. That's not advised, since Outreachy might be in the middle of a busy period. It's better to wait until December or July to upgrade Debian.

Make sure to stop the Outreachy website Docker containers before you reboot the system:

```
ssh -t dokku@outreachy.org ps:stop test
ssh -t dokku@outreachy.org ps:stop www
```
## Updating dokku

Updating Debian will also update your base version of dokku. That may mean you need to update some dokku plugins (either core plugins or external plugins).

Use the following commands to see what dokku plugins are installed:

```
dokku plugin:list
```

Read how to [manage dokku plugins](https://dokku.com/docs/advanced-usage/plugin-management/).

You also need to rebuild the applications to use any new buildpacks that are installed.

```
dokku ps:rebuild --all
```

## Restarting dokku

After you reboot the server, restart the Docker containers with the following commands:

```
ssh -t dokku@outreachy.org ps:start test
ssh -t dokku@outreachy.org ps:start www
```

# Updating Packages

## Updating Python packages

The Outreachy website is built using several different Python packages. The Django web framework is one such Python package. Python projects have different ways of automatically installing packages, but for this project, we use [pipenv](https://pipenv.readthedocs.io/en/latest/).

Python packages the website needs to install on are listed in the top-level file `Pipfile`. Pip uses this file to figure out what packages and what versions of packages to install. If you edit `Pipfile`, you'll see some of the other Python packages we use. For example, [django-ckeditor](https://github.com/django-ckeditor/django-ckeditor) is the Django package of [CKEditor](https://ckeditor.com/). It provides the rich-text WSIWIG editor for form fields used by Outreachy mentors.

The other file to be aware of is `Pipfile.lock`. Pipfile lists the important Python packages the website depends on. However, those packages also have dependencies on other Python packages. Pipfile.lock lists the versions of all the packages to install. It also lists the sha1 hash for the source code of each Python package. The sha1 hash ensures that if you try to reinstall packages, you'll always get the exact version you installed previously.

The pipenv documentation has [examples of how to upgrade packages](https://pipenv.readthedocs.io/en/latest/basics/#example-pipenv-upgrade-workflow). You'll need to run `pipenv shell` before any of these commands.

Upgrade all Python packages with this command:
```
pipenv update
```

If you want to update just one package, you can use this command:
```
pipenv update <pkg>
```

These commands will update `Pipfile` and `Pipfile.lock`. You'll need to commit both files.

## Syncing updated Python packages

When someone else makes a commit that updates the packages listed in the pipfile, when you pull those changes, you'll need to update your installed packages. Otherwise you may (or may not!) get an error whenever you try to run a manage.py command. The error might only be triggered if you view a particular page that runs Python code that depends on those installed packages.

To sync your installed pipenv packages with any changes made in the Outreachy GitHub repository, run the following command:

```
pipenv sync
```

## Updating node.js packages

The Outreachy website relies on several node.js packages. You can update those packages with the node.js package manager, npm:

```
npm update
```

This commands will update `package-lock.json`. You will need to commit that file.

## Testing and pushing updates

Before upgrading anything, you should understand how to test upgrades.

First, test your updates locally:

1. **Run the test suite.** Make sure no new errors or warnings occur. Warnings about deprecated functions or deprecated Python modules are a sign you may need to update the Outreachy website code to align with the updated versions of Python packages.

2. Start the web server for your local development environment.

3. **Test image uploading.**

We don't currently have tests for making sure Outreachy website image storage works. I don't think the test database has access to the image storage on the local machine. So we have to test manually on the local development environment via web browser.

You can test that image uploading works by changing your profile picture twice. You can change your profile picture through your account page [http://localhost:8000/account](http://localhost:8000/account). Change your profile, save your account details, go back to the account page, and you should see your new profile picture. Change the profile picture again, save, go back to the account page, and verify the second picture is shown.

4. **Test initial application submission.**

While we have tests for each part of the initial application form, the tests rely on setting up some data in the database manually. That means we need to manually test going through each application page in a browser.

Create a new Outreachy internship cohort. Set the date initial applications open to yesterday. (It's important to not set it to today, since initial applications open at 4pm UTC, and your current local time might be before that time.)

```
$ ./manage.py shell
>>> from home import factories
>>> current_round = factories.RoundPageFactory(start_from='initial_applications_open', days_after_today=-1)
```

You can use your superuser account to fill out an initial application.

Open your web browser and go to `http://localhost:8000/eligibility/`.

Fill out the application form, using your knowledge of the [eligibility criteria](http://localhost:8000/eligibility/).

It's good to double check that the 'First step', 'Next Step', and 'Previous Step' buttons all work.

To test all the form pages, answer 'yes' to the following questions:

2-1: Are you a citizen, national, or permanent resident of the United States of America?
2-2: Will you be living in the United States of America at any time from April 20, 2024 to August 21, 2024?
7-1: Are you (or will you be) a university or college student?
7-2: Are you (or will you be) enrolled in a coding school or self-paced online courses?
7-3: Are you (or will you be) an employee?
7-4: Are you (or will you be) a contractor?
7-5: Are you (or will you be) a volunteer?

Once your initial application is submitted, confirm that it shows up on your [Outreachy dashboard](http://localhost:8000/dashboard/).

5. **Test your changes on the test web server.**

Next, you'll need to push your changes to the Outreachy test web server, and test out how they deploy in a production environment. Sometimes when code is run on a web server, it behaves differently than when it's run locally. Pushing to the test web server allows you to try the code at different times in the Outreachy application and internship, without confusing Outreachy participants.

Do note however, that Google search has picked up on the test website, so we should avoid having different dates between the two sites. FIXME: figure out how to set robots.txt differently for when we're deploying to the test website.

If you don't already have ssh access to the test web server, ask Sage to set it up. Once you have ssh access, you can run the following command:

```
git remote add dokku-test dokku@outreachy.org:test
```

You may need to clone the production database to the test website. See the 'Updating the test database' section in `docs/dokku-setup.md`.

Then you can push your changes to the test website by running this command:

```
git push dokku-test +BRANCH-NAME:master
```

BRANCH-NAME should be the name of the git branch you are currently testing your updates on. If you are testing on your master branch, you should remove the `+BRANCH-NAME:` part of the command.

When you push to the test server, it will automatically apply any Django database migrations.

You can view the test website at [https://test.outreachy.org](https://test.outreachy.org). Since the production database is copied to the test website, you can log into the website with your normal Outreachy website account.

From there, test steps 2-4 again. When it comes to running Django shell scripts, you can start a shell on the test web server with this command:

```
ssh -t dokku@outreachy.org run test env --unset=SENTRY_DSN python manage.py shell
```

# Updating Python versions

## Picking a Python version

It's important that we find a new Python version that is going to receive bug fix and security updates for the next 6 months. That's important because the Outreachy website only moves off Python major versions in December and July (when the website is not under heavy use).

It's important not to pick a Python version that is too new. We don't want to run the Python version that is currently under feature development.

We also don't want to run a Python version that is not yet included in Linux distributions.

The Outreachy webserver runs Debian stable. Make sure the new Python version is available for Debian stable.

We also want to make sure other Outreachy website developers have that Python version available. Otherwise they may not be able to test their work locally.

First, check the Python development roadmap to see which versions will be in bugfix status for the next six months:

[https://devguide.python.org/versions/](https://devguide.python.org/versions/)

Next, check to see which Linux distributions have that Python version available:
 - [Debian stable release](https://packages.debian.org/search?keywords=python3&searchon=names&suite=stable&section=all)
 - [Debian release cycle](https://www.debian.org/releases/)
 - [Fedora packages](https://packages.fedoraproject.org/search?query=python3)
 - [Fedora release cycle](https://docs.fedoraproject.org/en-US/releases/)

Pick a version of Python that is in the bugfix state for the next six months, and is included in Debian stable and the previous Fedora release.

Make sure to install that version of Python on your local development machine. That may mean you need to update your system to a new release of your Linux distribution.

Remember that Python version number you selected, and read the next section.

## Dokku management of Python versions

The Outreachy web server uses Dokku to manage the version of Python installed in the Docker container the website runs in.

Dokku uses the "buildpacks" from Heroku to find the correct version of Python to install. Think of buildpacks as a series of scripts that download and install programming language files. Heroku has buildpacks for many different programming languages. The Outreachy website uses Python and Node.js Heroku buildpacks.

When you want to update the version of Python that the production server is running, you'll need to:

1. Update herokuish using aptitude on the server:

```
$ ssh root@www.outreachy.org
# aptitude update
# aptitude install herokuish
```

Docker might complain that some images are still running. That's fine, because we want to leave them running until we restart them with new Python versions.

2. Find the [latest minor version of Python that Heroku supports](https://devcenter.heroku.com/articles/python-support#supported-runtimes). For example, if you choose to install Python 3.11, the latest minor version of Python that Heroku supports might be Python 3.11.7. Each minor version includes bug fixes and updates, so you want to have the latest minor version you can.

Change the Python version number in [runtime.txt](https://github.com/outreachy/website/blob/master/runtime.txt) to match the version of Python you want deployed on the web server.

3. You will need to update the [Heroku Python buildpack version](https://devcenter.heroku.com/articles/python-support#checking-the-python-buildpack-version). Change the version in [.buildpacks](https://github.com/outreachy/website/blob/master/.buildpacks) to match the URL of the [latest Python buildpack GitHub tag](https://github.com/heroku/heroku-buildpack-python/tags). Use the format in the `.buildpack` file.

4. Commit both files (`runtime.txt` and `.buildpack`).

Delete your virtual environment and rebuild it with the new runtime.txt. Start your virtual environment, and make sure it's using the updated Python version.

Run the test suite and manually test specific functionality, as described in the 'Testing and pushing updates' section above.

5. Deploy to the Outreachy test server. DO NOT DEPLOY TO PRODUCTION WITHOUT TESTING ON THE TEST SERVER FIRST. In the deployment log, you should see lines like:

```
=====> Downloading Buildpack: https://github.com/heroku/heroku-buildpack-python
=====> Detected Framework: Python
-----> Using Python version specified in runtime.txt
-----> Stack has changed from heroku-18 to heroku-20, clearing cache
remote: cp: cannot stat '/tmp/build/requirements.txt': No such file or directory
-----> Installing python-3.9.7
```

You'll note in this log that the server picked up on the updated herokuish package (`Stack has changed from heroku-18 to heroku-20, clearing cache`).

Also note that dokku is installing python-3.9.7, which was the latest Python version available through Heroku as of the time this section was written.

Don't worry about the error saying there's no requirements.txt. We use pip, so we don't have a requirements.txt.

6. Test the updated code on the test server. Make sure you can change your account picture, see the community CFP page, edit a Wagtail page like the home page, etc.

7. Deploy to the production server.

# Updating Node.js versions

If you want to update the version of Node.js that the production server is using, there are several different things you'll need to know.

Dokku uses the "buildpacks" from Heroku to find the correct version of Node.js to install. Think of buildpacks as a series of scripts that download and install programming language files. Heroku has buildpacks for many different programming languages. The Outreachy website uses Python and Node.js Heroku buildpacks.

When you want to update the version of Node.js that the production server is running, you'll need to:

1. Update the [Heroku Node.js buildpack version](https://devcenter.heroku.com/articles/nodejs-support#node-js-runtimes). Change the Node.js version in the [.buildpacks file](https://github.com/outreachy/website/blob/master/.buildpacks) to match the URL of the [latest Node.js buildpack GitHub tag](https://github.com/heroku/heroku-buildpack-nodejs/tags). Use the format in the `.buildpack` file.

2. Commit `.buildpack`.

3. Deploy to the Outreachy test server. DO NOT DEPLOY TO PRODUCTION WITHOUT TESTING ON THE TEST SERVER FIRST. In the deployment log, you should see lines like:

```
=====> Downloading Buildpack: https://github.com/heroku/heroku-buildpack-nodejs
=====> Detected Framework: Node.js
       
-----> Creating runtime environment
       
       NPM_CONFIG_LOGLEVEL=error
       NODE_VERBOSE=false
       NODE_ENV=production
       NODE_MODULES_CACHE=true
       
-----> Installing binaries
       engines.node (package.json):  unspecified
       engines.npm (package.json):   unspecified (use default)
       
       Resolving node version 14.x...
       Downloading and installing node 14.17.6...
       Using default npm version: 6.14.15
```

You'll note in this log that dokku is installing node version 14.x, which was the latest Stable version of Node.js available through Heroku as of the time this section was written.

4. Test the updated code on the test server. Make sure you can change your account picture, see the community CFP page, edit a Wagtail page like the home page, etc.

5. Deploy to the production server.

## Updating postgres

Each dokku container can run a different version of postgres (an open source database). dokku will not automatically update your postgres versions. You will need to do that manually.

You can see which versions of postgres are running on the different website containers by running this command:

```
dokku postgres:info www-database
```

You can also replace www-database with the name of the database used in the test website.

### Testing postgres updates

First, export the Outreachy website database using the current postgres plugin version:

```
dokku postgres:export www-database > www-database.export
```

To make more recent versions of postgres available to the Docker containers, you'll need to update the dokku postgres plugin. You can see which version of the plugin you're running with this command:

```
dokku plugin:list
...
  postgres             1.4.12 enabled    dokku postgres service plugin
``` 

Look to see what the [latest version of the postgres plug in](https://github.com/dokku/dokku-postgres) is. As of when this section was written, the latest version is 1.36.1. Update the postgres plug in with this command:

```
dokku plugin:update postgres 1.36.1
```

Next, we need to test whether moving to a new postgres version works. We want try the new postgres version out on the test database first.

Make a new database with the updated postgres plugin:

```
dokku postgres:create test-database
```

Import the www-database export into the newly created database:

```
cat www-database.export | dokku postgres:import test-database
```

Once the database is created, you should see in the output which postgres version it's using. You can also use the `dokku postgres:info DATABASE` command to see the postgres version.

Now, stop the test website Docker container:

```
dokku ps:stop test
```

Unlink the old test database from the test Docker container:

```
dokku postgres:unlink test-database-updated-2024-01-07 test
```

Link the updated database into the test Docker container:

```
dokku postgres:link test-database test
```

Promote the updated database:

```
dokku postgres:promote test-database test
```

DO NOT destroy the old test database just yet!

Restart the test Docker container:

```
dokku ps:restart test
```

Check the postgres version running of the test database is a newer version:

```
root@outreachy-website:~# dokku postgres:info test-database
=====> test-database postgres service information
...
       Status:              running                  
       Version:             postgres:16.1            
```

??? - I'm not clear whether we needed to rebuild the Docker containers, or where that rebuild should have happened. So you might need this command somewhere above:

```
dokku ps:rebuild test
```

Manually test that the Outreachy test website works. See a list above for what aspects to test.

Once you are satisfied, it's time to upgrade the Outreachy production database.

### Deploying postgres updates

(Optional) If you have upgraded the dokku postgres plugin, and the test website was running a very old version of postgres, you may need to downgrade the dokku postgres plugin in order to export the database:

```
dokku plugin:update postgres 1.4.12
```

Stop the Outreachy website Docker container:
```
dokku ps:stop www
```

Export the www-database (note, this may be a good time to export it to your local system as well for a brief back-up):
```
dokku postgres:export www-database > www-database.export
```

(Optional) If you're updating from a very old version of postgres, update the dokku postgres plugin to the latest version:
```
dokku plugin:update postgres 1.36.1
```

Then follow similar steps you used on the test database:

```
dokku postgres:create www-database-updated
cat www-database.export | dokku postgres:import www-database-updated
dokku postgres:unlink www-database www
dokku postgres:link www-database-updated www
dokku postgres:promote www-database-updated www
dokku ps:rebuild www
dokku ps:start www
```

# Debugging errors

# Debugging package installs

You can check to see which packages are installed with the following command:

```
pipenv graph
```

You can view the source code of any installed package with the following command:

```
pipenv open <pkg>
```

# Debugging migration errors

Sometimes you'll get an error when you migrate or run code that says 'it appears to be a stale .pyc file'. How you fix this is by removing the cache of code that has been pre-compiled to CPython's byte code format.

Run this command:

```
rm home/migrations/*.pyc
```

You may have to remove other pycache folders that contain stale pre-compiled code.

# Why Django?

We evaluated a couple different choices:
 - CiviCRM
 - Wordpress
 - Red Hen
 - Django

CiviCRM proved too clunky to use, and ultimately their data model didn't necessarily fit our data models. Wordpress might have been fine with a template plugin and would have good user experience, but with everything we wanted to do, we felt we would ultimately outgrow Wordpress.

There are other proprietary tools for tracking sponsorship information, but since Outreachy is a project under the Software Freedom Conservancy and the Outreachy organizers believe in the power of free and open source, we have decided not to use proprietary software wherever possible.

Django fit our needs for flexibility, data model definition, and future use cases. However, the Django admin interface is pretty clunky and intimidating. We wanted to have a very easy way for all our organizers to quickly edit content. The Wagtail CMS plugin provides a nice user interface and template system, while still allowing programmers to fully use Django to implement models. It also provides internal revision tracking for page content, which means we can easily roll back content changes from the wagtail admin web interface if necessary.

# Creating blog posts

## Django code method

This method of publishing a blog post is best suited for blog posts that need to access information from the Outreachy website database. Examples include blog posts that reference internship cohort dates. When you change the date in the Outreachy Django admin interface, the date will change in any blog posts created this way.

You will need to edit four different files to create a blog post:

```
home/feeds.py
home/templates/home/blog/YOURBLOGPOST.html
home/urls.py
home/views.py
```

### HTML blog file

```
home/templates/home/blog/YOURBLOGPOST.html
```

This html file contains your blog post, written in HTML and <a href="https://docs.djangoproject.com/en/4.2/ref/templates/language/#top">Django templating language</a>. The HTML file must be located in the directory `home/templates/home/blog/`.

The most basic blog post you can write is as follows:

```
{% extends "base.html" %}
{% load static %}

{% block title %}
Example blog post
{% endblock %}

{% block content %}
{% load humanize %}

<h1>Example blog post</h1>
<p>This is my example blog post.</p>

{% endblock %}
```

You'll see this is a mix of two lines of HTML and a lot of Django templating language code. You can read more about what each line:
 - `{% extends "base.html" %}` - tells Django to use the standard headers and footers used across all Outreachy website pages.
 - [`{% load static %}`](https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#static) - tells Django to load static files (like pictures from the Outreachy website code base).
 - [`{% load humanize %}`](2023-08-08-initial-applications-open.html) - Used to convert integers stored in the Django database to human-readable words (e.g. showing "two" instead of "2" or "$8,000" instead of "$8000").
 - [`{% endblock %}`](https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#block) - Django templating language defines different types of "blocks". Every type of block ends with an `{% endblock %}` tag.
 - `{% block title %}` - converts the string into the title used in the HTML head section - i.e. the title that's displayed on your web browser titlebar or tab title.
 - `{% block content %}` - Any HTML content between this block and the endblock is displayed in the HTML body section - i.e. it will be displayed in your web browser window.

The easiest way to create a blog HTML file is to copy a similar blog post, and edit it.

For example, if I want to create a blog post announcing initial applications are open for the May 2024 internship cohort, I might copy the HTML from the December 2023 cohort's blog post on the same subject:

```
cp home/templates/home/blog/2023-08-08-initial-applications-open.html home/templates/home/blog/2024-01-15-initial-applications-open.html
```

Then I would edit the newly created HTML, and update it for the new internship cohort. I would need to:
 - update the blog post published date to be today's date
 - change the internship cohort name to the correct one (e.g. May to August 2024 cohort)
 - search for any date strings to change with the regex `Jan\|Feb\|Mar\|Apr\|May\|Jun\|Jul\|Aug\|Sep\|Oct\|Nov\|Dec\|2023\|2024`
 - make sure the URLs for the date time converter website match the new live chat dates
 - check that the eligibility rules about students from different hemispheres are correct for this cohort
 - update the dates for the applicant live chat Q&A sessions
 - see if you want to change any embedded videos to point to more recent live chats

### URLs

```
home/urls.py
```

The `home/urls.py` file contains regular expressions that match against the URL that a remote viewer is trying to look at. It translates the URL into a Python function call in `home/views.py`. A URL can also contain encoded variables, which are passed to the Python function.

In this case, we need to create a URL that will represent our blog post. I like to make sure blog URLs have both a date and include at least part of the blog post title.

Here is what the line for adding this new blog post would look like:
```
    re_path(r'^blog/2024-01-15/may-2024-initial-applications-open/$', views.blog_2024_01_15_initial_applications_open, name='2024-01-initial-applications-open'),
```

The first part of the function call is the URL to match against. That's what will be in your web browser's address bar when you visit this blog post.

The second part of the function lines is what Python function to call. In this case, Django will call into the code in `home/views.py`, into a Python function called `blog_2024_01_15_initial_applications_open`.

The third part of the function is a shortcut for this URL. It means if you are writing an HTML page, you can ask Django to look up the URL associated with that shortcut.

### Side note about Django URL shorts

For example, assume we have the following URL pattern in home/urls.py:

```
re_path(r'^apply/eligibility/$', views.eligibility_information, name='eligibility-information'),
```

An inefficient way to reference the eligibility page would be to hard-code the link directly:

```
<p>Check our <a href="https://www.outreachy.org/apply/eligibility/">eligibility criteria</a> before you apply.</p>
```

However, if we ever decided to change the URL for eligibility page, that link would be broken, and would lead to a 404 error. For example, we might want to move the URL from `https://www.outreachy.org/apply/eligibility/` to `https://www.outreachy.org/apply/eligibility-rules/`

A more efficient and resilient way to include a link is to use the [Django URL tag](https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#url):

```
<p>Check our <a href="{% url 'eligibility-information' %}">eligibility criteria</a> before you apply.</p>
```

This is a best practice to use in templating, because the URL path might change, and you don't want to update every single HTML template that references it.

### Views

```
home/views.py
```

In `home/urls.py`, we had a line that told Django which Python function to call when the blog post URL was accessed:

```
    re_path(r'^blog/2024-01-15/may-2024-initial-applications-open/$', views.blog_2024_01_15_initial_applications_open, name='2024-01-initial-applications-open'),
```

Now we need to write that Python function in `home/views.py`. Django handles a lot of the mundane processing of HTML GET or POST requests, but we do need to add a few function calls.

First, we need to tell Django which HTML template file to render. The simplest (but incorrect) function we could create is this one:

```
def blog_2024_01_15_initial_applications_open(request):
    return render(request, 'home/blog/2024-01-15-initial-applications-open.html')
```

This would produce incorrect output, because the blog post would not display dates from the May 2024 internship cohort. If you look at the HTML template, you can see lines where we reference that cohort as the <a href="https://docs.djangoproject.com/en/4.2/ref/templates/language/#variables">variable</a> `current_round`:

```
<p>📅 Important dates:
<ul>
	<li>{{ current_round.initial_applications_open }} at 4pm UTC - initial application opens</li>
	<li>{{ current_round.initial_applications_close }} at 4pm UTC - initial application deadline</li>
	<li><a href='#important-dates'>Full Outreachy schedule</a></li>
</ul>
</p>
```

If you try to view the blog post, you'll see the page doesn't show any dates in that list, only "at 4pm UTC".

To fix that, we need to update the Python function to look up the correct cohort, and then pass that cohort object into the template rendering function. To find the right May 2024 cohort, we ask the database to find an internship cohort where the interns start after January 1, 2024 and the interns end before September 1, 2024. You can also use an exact date filter instead if you want, but this is more resilient if the dates move by a few days.

The resulting correct code in `home/views.py` would be this:
```
def blog_2024_01_15_initial_applications_open(request):
    try:
        current_round = RoundPage.objects.get(
            internstarts__gte='2024-01-01',
            internends__lte='2024-09-01',
        )
    except RoundPage.DoesNotExist:
        current_round = None
    return render(request, 'home/blog/2024-01-15-initial-applications-open.html', {
        'current_round': current_round,
        })
```

We wrap the call to find the cohort in the database in a try-except block. This handles the case where the Django database can't find an object that matches your query. For example, this could be because your local testing database doesn't have a RoundPage object that represents the May 2024 cohort. You might need to create it using the internship scenarios section above.

You can read more about why need excepting handling in the [Django get() method documentation](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#django.db.models.query.QuerySet.get). See also [this tutorial on Python exception handling](https://www.w3schools.com/python/python_try_except.asp).

### Testing the blog post

Now that the URL and view function is added, you can test your code by starting the Django web server (runserver command) and then going to the localhost URL for that blog post:

```
http://localhost:8000/blog/2024-01-15/may-2024-initial-applications-open/
```

If you get an error, you may have a bug in either the Python functions or the template code. Common errors are things like forgetting to end a block, forgetting to end an if statement, or mistyping a URL shortcut.

If you get a 404, it probably means you either have the URL wrong, or your pattern in `home/urls.py` is incorrect (or in the incorrect place, since URL patterns are evaluated from the top down).

### Blog post feed

In our Django website, there is a [blog index page](https://www.outreachy.org/blog/) that displays all blog posts. That page displays links to both Django code based blog posts and blog posts written in the Wagtail CMS. The blog posts written in Wagtail (as a child page of the blog index page) are automatically added to the blog index page. The Django code based blog posts must be added manually.

The Python code that creates our [blog index page](https://www.outreachy.org/blog/) and [blog post RSS feed](https://www.outreachy.org/blog/feed/) is in `home/feeds.py`. This code creates a new Wagtail "PseudoPage" for every Django-code based blog post. A PseudoPage can be referenced by Wagtail, but is not shown as an editable page in the Wagtail admin interface. The blog's PseudoPage is inserted into our website's Wagtail page hierarchy as a child of the blog index page. Any pages that are children of a blog post index page will have their link and title added to the blog index page.

In `home/feeds.py` we will need to manually add our blog post to the blog post index and RSS feed:

```
items.append(PseudoPage(
    title='Outreachy May 2024 internship applications open',
    full_url=reverse('2024-01-initial-applications-open'),
    owner=author,
    first_published_at=pacific.localize(datetime.datetime(2024, 1, 15, 21, 15, 0)),
    last_published_at=pacific.localize(datetime.datetime(2024, 1, 15, 21, 15, 0)),
))
```

The `title` should be the same as the title used in the HTML template. This is best practice, but not required to match.

The `full_url` should be the URL shortcut used in `home/urls.py`. It must match the exact shortcut string.

The `owner` field is used to tell Wagtail who authored the PseudoPage. We currently set all blog posts to be authored by Sage's account. You could use a database look-up to set the owner to your own account. However, we don't tell Wagtail to display the blog post author in the blog post index page, so it won't show up anywhere visible.

The `first_published_at` field is used to set the date when the blog is first pushed to the website. This also controls when the blog post shows up in people's chronological RSS feeds.

If you make blog post changes, you can modify the `last_published_at` field. This tells RSS readers that they should re-fetch the contents of the blog post.

If you modify a blog post, it's best practice to note what changes were made in the HTML template. For example, in our blog post about Outreachy's response to COVID-19, we noted when changes were made, and what sections were added or modified:

```
<h1>Outreachy's Response to COVID-19</h1>

<p><i>Date: March 27, 2020</i></p>
<p><i>Last updated: May 1, 2020</i> - See the "New policies for students" section below.</p>
```

### Committing your new blog post

Make sure to use git to commit the four files you've either created or modified:

```
home/feeds.py
home/templates/home/blog/YOURBLOGPOST.html
home/urls.py
home/views.py
```

### Testing on the Outreachy test server

You can also push your code to the Outreachy test website server.

Run the following command to add a new git remote branch for the test server:

```
git remote add dokku-test dokku@outreachy.org:test
```

This tells git to push code to the dokku user account. The dokku username is important because the server won't let you push code under your own user account. The destination string `outreachy.org:test` tells the server that we're pushing code for the outreachy.org website, and specifically the Docker container named `test`. This Docker container runs the code for `test.outreachy.org`.

Sage will need to give your website server account permission to directly push code. That is a separate permission from your account's permission to run a Django shell.

Once you push your code, you'll see a lot of messages about dokku re-building the test container. If you come across any error messages, let Sage know and we'll debug them together.

Once the code is deployed, go to the [blog index page on the test website](https://test.outreachy.org/blog/). Check the link to your blog is there. Click the link and check your blog is displayed properly.

### Pushing to GitHub

Then you'll need to either open a pull request on GitHub, or push directly to GitHub.

### Deploying on the live site

Run the following command to add a new git remote branch for the production (`www`) code base:

```
git remote add dokku-www dokku@outreachy.org:www
```

Then you can push your code and deploy it.
