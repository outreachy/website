The outreachy-website server uses dokku to host the Django/Wagtail server.
When in doubt, reference the dokku documentation for getting dokku set up:
 - [Dokku installation instructions](http://dokku.viewdocs.io/dokku/getting-started/installation/)
 - [Dokku app deployment instructions](http://dokku.viewdocs.io/dokku/deployment/application-deployment/)

On the server, you'll need to setup the dokku postgres plugin:
```
$ sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git
```

For the remaining steps, you can either run dokku commands on the server, or run them on your local computer using ssh. All commands that need to run on the server will start with:
```
$ ssh dokku@$DOMAIN
```
(where you need to replace "$DOMAIN" with the name of the server you're using that has dokku installed) but if you're running them directly on the server then you can replace that with
```
$ dokku
```

If you need help with any dokku commands at any time, you can ask for the documentation with a command like this:
```
$ ssh dokku@$DOMAIN config:help
```

The next step is to ask Dokku for space to deploy a new app, which we'll call $APP in this document:
```
$ ssh dokku@$DOMAIN apps:create $APP
```

Whatever name you use for $APP, if it doesn't have any periods in it (like "outreachy-test" or "www"), Dokku will append the domain name you've configured as its default. For example, on the live site, we use "www", and let Dokku append ".outreachy.org" to that.

Next, you can either create a new database, or clone an existing database:

 - Create an empty PostgreSQL database to store all the site data:
   ```
    $ ssh dokku@$DOMAIN postgres:create $APP-database
    ```
 - With the outreachy.org website, we have the production database and the test database. You can clone the production database into a new test database with the command:
   ```
   $ ssh dokku@$DOMAIN postgres:clone $PRODUCTION-database $TEST-database
   ```

Now that we have a database, we can link the www Django app to the www-database postgres database:
```
$ ssh dokku@$DOMAIN postgres:link $APP-database $APP
```

If you're curious, you can ask Dokku to show you the configuration for the database, including the internal environment variable which is a URL containing a unique password to access the database:
```
$ ssh dokku@$DOMAIN config $APP
```

Images
------

Each time we push to dokku, or change the configuration, the docker container that hosts the Outreachy website is destroyed and re-deployed.
By default, any images we've uploaded through wagtail or django will be destroyed as well.
There are two ways to work around this: setting up cloud storage on Rackspace, or setting up persistent storage in dokku, which will simply use the server's disk space.
We expect that users who can upload images will be either community coordinators, mentors, or interns.
In the future, when we migrate the application system over to wagtail and django, we may also have applicants uploading files like resumes (which are optional).
One threat model to keep in mind is a group of malicious people trying to flood the application system with applications and large files.
Putting a limit on the file size might help, but won't stop such an attack.
For now, we'll go with [dokku persistent storage](http://dokku.viewdocs.io/dokku/advanced-usage/persistent-storage/) with the help of a package called dj-static.

Dokku will create a new directory /var/lib/dokku/data/storage, and we create a subdirectory for the www dokku app (our wagtail/django app) on the server, which bind mounts django's /app/media (default storage in the container) to /var/lib/dokku/data/storage/$APP:
```
$ ssh dokku@$DOMAIN storage:mount $APP /var/lib/dokku/data/storage/$APP:/app/media
```
(Note: if you are running a test app, and you want that app to have access to the production app's media, you can replace the second $APP with your production app's name. Only do this if you trust your test app users to not delete all your media!)

Configure environment variables
-------------------------------

Clone the git repo:
```
$ git clone git@github.com:outreachy/website.git outreachy
$ cd outreachy
```

In this repo, we've told Django to get certain settings from environment variables. You can find all the environment variables we rely on in `outreachyhome/settings/production.py`. In order to tell Django to use that file, we also have to set `DJANGO_SETTINGS_MODULE`.

Most importantly, for a public-facing deployment, we need a unique random value for `SECRET_KEY`. You can generate it any way you want but we use `pwgen`.
```
$ ssh dokku@$DOMAIN config:set $APP DJANGO_SETTINGS_MODULE=outreachyhome.settings.production SECRET_KEY="`pwgen -sy 50 1`"
```

If you see an error message like `xargs: unmatched double quote; by default quotes are special to xargs unless you use the -0 option`, it means pwgen came up with a password with a quote or single quote in it. You'll need to set the SECRET_KEY again, because Dokku doesn't shell-escape these variables.

You also need to tell Django which hostname it's being deployed at or it will return `400 Bad Request` without telling you why (although we've configured it to at least log the error in `dokku logs $APP`). That's probably something like this:
```
$ ssh dokku@$DOMAIN config:set $APP ALLOWED_HOSTS=$APP.$DOMAIN
```

The Outreachy website sends outgoing mail (for example from the contact form), so you'll need a mailserver that can handle SMTP. You can skip this if you want, but anything trying to send email will fail. You can also come back to this step and do it later.
Set up Django to send email through your mail server by filling in these variables with your own account information:
```
$ ssh dokku@$DOMAIN config:set $APP EMAIL_HOST=mailhost EMAIL_PORT=port EMAIL_USE_SSL=True EMAIL_HOST_USER=emailusername EMAIL_HOST_PASSWORD=password
```

Deploy
------

Now, finally! we can deploy the app on the server, following the dokku "Deploy the app" section:

On the local box, git commit, and add the dokku as a remote:
```
$ git remote add dokku dokku@$DOMAIN:$APP
$ git push dokku HEAD:master
```
(Note: dokku will only pull from the master branch on the git repo when it's deploying an app.)

Apply all the Django migrations we've set up:
```
$ ssh dokku@$DOMAIN run $APP python manage.py migrate
```

Create Django Superuser
=======================

If you created a new database (not cloned an existing database) we need to follow the Django directions to create a superuser. If you are running this from your local computer, for this ssh command you need to run `ssh -t` or you won't be able to type answers to the questions this command prompts you with.
```
$ ssh -t dokku@$DOMAIN run $APP python manage.py createsuperuser
```

SSL certificate
---------------

Follow [the dokku-letsencrypt plugin instructions](https://github.com/dokku/dokku-letsencrypt) to add a Let's encrypt SSL certificate.

Add a cron job to auto-renew the certificate:
```
$ ssh dokku@$DOMAIN letsencrypt:cron-job --add
```

Updating the test database
--------------------------

Periodically, you'll want to import the live database to the test site, in order to try a new migration or test new views code. You could export the database as a backup, but that won't work if the schema used on the test site differs from the live site. Instead, we need to clone the live site's database and do a little dance to link it into the test site.

First, clone the live database (www-database):
```
ssh dokku@outreachy.org postgres:clone www-database test-database-updated-2018-02-13
```

Next, link the cloned database to the dokku test container:
```
ssh dokku@outreachy.org postgres:link test-database-updated-2018-02-13 test
```

We promote the cloned database to be used by the test container:
```
ssh dokku@outreachy.org postgres:promote test-database-updated-2018-02-13 test
```

Then we unlink the older database (use whatever was the old name):
```
ssh dokku@outreachy.org postgres:unlink test-database-updated-old test
```

You can always figure out which databases are linked with this command:
```
ssh dokku@outreachy.org postgres:list
```

Then you can `git push` to the test site, migrate, and test any updated views.

Finally, we can destroy the older database (use whatever was the old name):
```
ssh dokku@outreachy.org postgres:destroy test-database-updated-old
```

Sending mass emails
-------------------

When you need to send a mass email manually, you can do so through the dokku interface to the Django shell. It's useful to run the commands under the test database, because it will simply print out the messages, rather than sending them. Make sure to migrate the test database to an updated version from the live site, using the instructions above.

Then, ssh into the test server shell, and run the commands you want. In this example, we'll simulate clicking the "Contributor Deadline Email" button on the staff dashboard:

```
$ ssh -t dokku@www.outreachy.org run www env --unset=SENTRY_DSN python manage.py shell
Python 3.6.3 (default, Nov 14 2017, 17:29:48) 
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from django.test import Client
>>> from django.contrib.auth.models import User
>>> c = Client(HTTP_HOST='www.outreachy.org') # set this to the domain you expect to be on
>>> c.force_login(User.objects.filter(is_staff=True, comrade__isnull=False)[0])
>>> c.post('/email/contributor-deadline-reminder/', secure=True)
```

If this is run on the test server, you should see lots of email bodies get printed; the live server will send them to their intended recipients, instead. Either way, if it worked, you should eventually see:

```
<HttpResponseRedirect status_code=302, "text/html; charset=utf-8", url="/dashboard/">
```

Sending mass emails manually
----------------------------

```
$ ssh -t dokku@www.outreachy.org run www env --unset=SENTRY_DSN python manage.py shell
>>> from home.models import *
>>> from django.core.mail import send_mail
>>> current_round = RoundPage.objects.latest('internstarts')
>>> interns = current_round.get_approved_intern_selections()
>>> request = { 'scheme': 'https', 'get_host': 'www.outreachy.org' }
>>> subject = '[Outreachy] Important information'
>>> body = '''This is a multiline message.
... 
... This is the second line.
... 
... This is the third line.
... 
... This is the final line.
... 
... Sage Sharp
... Outreachy Organizer'''
>>> for i in interns:
...     emails = [ i.applicant.applicant.email_address() ]
...     for m in i.mentors.all():
...             emails.append(m.mentor.email_address())
...     send_mail(message=body.strip(), subject=subject.strip(), recipient_list=emails, from_email=Address("Outreachy Organizers", "organizers", "outreachy.org"))
... 
```
