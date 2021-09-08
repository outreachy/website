This repository is for the code that comprises the [Outreachy website](https://www.outreachy.org).

# What is Outreachy?

Outreachy provides remote internships. Outreachy supports diversity in open source and free software!

Outreachy internships are 3 months long. Interns are paid an internship stipend of $6,000 USD.

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

# Updating Packages

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

## Syncing updated packages

When someone else makes a commit that updates the packages listed in the pipfile, when you pull those changes, you'll need to update your installed packages. Otherwise you may (or may not!) get an error whenever you try to run a manage.py command. The error might only be triggered if you view a particular page that runs Python code that depends on those installed packages.

To sync your installed pipenv packages with any changes made in the Outreachy GitHub repository, run the following command:

```
pipenv sync
```

# Updating Python versions

If you want to update the version of Python that the production server is using, there are several different things you'll need to know.

Dokku uses the "buildpacks" from Heroku to find the correct version of Python to install. Think of buildpacks as a series of scripts that download and install programming language files. Heroku has buildpacks for many different programming languages. The Outreachy website uses Python and Node.js Heroku buildpacks.

When you want to update the version of Python that the production server is running, you'll need to:

1. Update herokuish using aptitude on the server:

```
$ ssh root@www.outreachy.org
# aptitude update
# aptitude install herokuish
```

2. Find the [latest version of Python that Heroku supports](https://devcenter.heroku.com/articles/python-support#supported-runtimes). Change the version in [runtime.txt](https://github.com/outreachy/website/blob/master/runtime.txt) to match the latest version of Python.

3. You will need to update the [Heroku Python buildpack version](https://devcenter.heroku.com/articles/python-support#checking-the-python-buildpack-version). Change the version in [.buildpacks](https://github.com/outreachy/website/blob/master/.buildpacks) to match the URL of the [latest Python buildpack GitHub tag](https://github.com/heroku/heroku-buildpack-python/tags). Use the format in the `.buildpack` file.

4. Commit both files (`runtime.txt` and `.buildpack`).

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
