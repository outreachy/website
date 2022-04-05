Setting up dokku
---

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

Adding website server SSH access
---

If you want to give website server SSH access to another person:

1. Ask them to generate an ssh key

2. Copy their key from your local system to the website server's .ssh directory:

```
scp /tmp/NEW-KEY.pub root@www.outreachy.org:/root/.ssh/
```

3. Log into the website server:

```
ssh root@www.outreachy.org
```

4. Add their key to the SSH list of authorized keys:

```
cat .ssh/NEW-KEY.pub >> .ssh/authorized_keys
```

5. Ask the person to log into the website server to test their SSH access with this command:

```
ssh root@www.outreachy.org
```

Adding dokku access
---

Access to run dokku commands is separate from website server access. You can run dokku commands without having webserver access. It's often useful for people who can ask dokku to deploy to debug dokku or postgres by running commands on the website server Linux command line.

Dokku has [documentation](https://dokku.com/docs/deployment/user-management/#user-management) about how to add users who can run dokku commands.

1. See who already has dokku ssh access by running this command on your local system:

```
ssh -t dokku@www.outreachy.org ssh-keys:list
```

2. Tell dokku to add the ssh key you already copied over to its list of authorized users:

```
ssh -t root@www.outreachy.org dokku ssh-keys:add NEW-USERNAME /root/.ssh/NEW-KEY.pub
```

3. Check that NEW-USERNAME is added as a dokku ssh user by listing the authorized ssh keys again:
```
ssh -t dokku@www.outreachy.org ssh-keys:list
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

In its default configuration, the `gunicorn` web server can only handle one request at a time. Ideally all requests would respond quickly and this wouldn't matter, but in practice it does. The documentation recommends that however many CPU cores you have, you should run 2-4 times as many worker processes. So if you have 8 cores and want to run twice as many worker processes, set this:
```
$ ssh dokku@$DOMAIN config:set $APP WEB_CONCURRENCY=16
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

After the first deploy, the Node and Python packages are cached, but sometimes this cache goes bad. In that case you can purge the cache before deploying again:

```
$ ssh dokku@$DOMAIN repo:purge-cache $APP
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

Updating dokku plugins
----------------------

Dokku has two types of plugins: core plugins and external plugins. Core plugins are updated when the base version of dokku is updated.

Upgrading the base dokku version doesn't automatically upgrade external plugins. The two external plugins we have are git-rev and letsencrypt.

You'll need to periodically update the dokku let's encypt plug in, following the instructions in the [README](https://github.com/dokku/dokku-letsencrypt#upgrading-from-previous-versions). You need to actually ssh into the machine; you can't run this command remotely:
```
dokku plugin:update letsencrypt
```

File upload size limits
-----------------------

To avoid denial of service attacks, it's important that the server reject attempts to upload files that are excessively large. In Dokku, the first line of defense against this attack is the nginx [`client_max_body_size`](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size) setting, which defaults to 1MB. But we allow people to upload their own profile photos and they often try to use pictures which exceed this limit, then get an inscrutable "413 Request Entity Too Large" error message.

There are two ways to address the UX issues this causes: either increase the size limit, or improve the error message. You can do both at the same time if you want.

Both ways require additional nginx configuration. Dokku documentation first covers how to replace their default nginx configuration wholesale, but I don't recommend that if you can avoid it, so instead, create a config snippet in `/home/dokku/$APP/nginx.conf.d/` as documented under ["Customizing via configuration files included by the default templates"](http://dokku.viewdocs.io/dokku/configuration/nginx/#customizing-via-configuration-files-included-by-the-default-tem).

To change the limit, add a line like this to the new config file:

```
client_max_body_size 5m;
```

To change the error page, add an [`error_page`](https://nginx.org/en/docs/http/ngx_http_core_module.html#error_page) setting like this:

```
error_page 413 /request-too-large
```

The `/request-too-large` path can be any path you want that's configured in Django. Then when nginx would serve up its own 413 response, it instead pretends like the visitor requested `https://www.outreachy.org/request-too-large` and returns whatever response Django generates for that URL. So you can reuse existing Django templates to make sure the error page matches the style of the rest of the site.

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

Figure out what the name of the old database linked to the test app is with this command:
```
ssh dokku@outreachy.org postgres:list
```

Then we unlink the older database (use whatever was the old name):
```
ssh dokku@outreachy.org postgres:unlink test-database-updated-old test
```

Then you can `git push` to the test site, migrate, and test any updated views.

Finally, we can destroy the older database (use whatever was the old name):
```
ssh dokku@outreachy.org postgres:destroy test-database-updated-old
```

Debugging
---

You can turn on dokku log verbosity by running:

```
ssh dokku@outreachy.org trace:on
```

Turn it off by running:

```
ssh dokku@outreachy.org trace:off
```

Sometimes postgres linking fails? If you have unlinked your old database and you get this error when you link in the new one `Unable to use default or generated URL alias`, then run the following command:

```
ssh dokku@outreachy.org config:unset --no-restart test DATABASE_URL DOKKU_POSTGRES_YELLOW_URL
```

Debugging Slow Database Queries
---

If the site is being slow and you don't know why, a good first guess is that some database query is the culprit, but which one is it? If `DEBUG=True` then the Django Debug Toolbar is very helpful, but often performance problems only show up on the live site, where debugging must be turned off for security reasons.

So instead you can tell Postgres to log queries that take longer than a certain amount of time.

```
ssh -t dokku@outreachy.org postgres:connect www-database
```

```
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

These log messages are supposed to be accessible like so:

```
ssh dokku@outreachy.org postgres:logs www-database -t
```

However that didn't work for reasons I don't understand, so I had to run this as root on the host server instead:

```
docker logs --tail 50 dokku.postgres.www-database
```

When you're done, don't forget to turn the logging back off:

```
ALTER SYSTEM RESET log_min_duration_statement;
```

Backing Up the Database
---

`ssh dokku@outreachy.org postgres:export www-database > outreachy-website-database-backup.sql`

This will give you a raw SQL database that you can use to reinstall the website if needed.


Resetting dokku
---------------

Sometimes after you do a server update, dokku is not serving the website. You can restart dokku by running this command:

```
ssh -t dokku@outreachy.org ps:restart www
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
>>> from home import models
>>> from django.core.mail import send_mail
>>> current_round = models.RoundPage.objects.latest('internstarts')
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
...     send_mail(message=body.strip(), subject=subject.strip(), recipient_list=emails, from_email=models.Address("Outreachy Organizers", "organizers", "outreachy.org"))
... 
```

# Marking interns as paid

If all interns can be paid:

```
>>> from home.models import *
current_round = RoundPage.objects.get(interstarts='YYYY-MM-DD')
>>> interns = current_round.get_in_good_standing_intern_selections()
>>> for i in interns:
...     try:
...             if i.finalmentorfeedback.payment_approved and not i.finalmentorfeedback.organizer_payment_approved:
...                     i.finalmentorfeedback.organizer_payment_approved = True
...                     i.finalmentorfeedback.save()
...     except FinalMentorFeedback.DoesNotExist:
...             pass
... 
>>> 
```

If you have a list of interns that have their payment authorized, but not all interns should be paid:

```
>>> emails = [ ... ]
>>> from home import models
>>> feedback = models.Feedback2FromMentor.objects.filter(intern_selection__applicant__applicant__account__email__in=emails).exclude(organizer_payment_approved=False).filter(payment_approved=True)
>>> for f in feedback:
...     f.organizer_payment_approved = True
...     f.save()
...
>>>
```

You can use the following regular expression command in vim to turn a list of interns in format "Name <email> # community" into a list of emails:

```
%s/^.*<\(.*\)>.*/"\1",/
```
