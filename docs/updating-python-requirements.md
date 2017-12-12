To update the Python packages that the Outreachy website depends on:

```
workon outreachy-django
pip freeze > requirements.txt
```

Do a git diff to make sure you've committed all changes to requirements.txt.
Remove the line `pkg-resources==0.0.0`

Then run this command to try updating all the listed packages:

```
grep -v '^\-e' requirements.txt | cut -d = -f 1  | xargs -n1 pip install -U
```

(The -e flag is for fetching Python packages from a specific remote repository, often associated with a particular git commit. Try to avoid this.)

See if the changes to the packages require you to run a migration on the website:

```
./manage.py migrate
```

(Note: you only need to run makemigrations if you make changes to the code. `migrate` is the only required step for upgrading packages.)

Check the changes by running the Python website locally:

```
./manage.py runserver
```

FIXME: set up a test server as well.

After you've tested the website (FIXME add a test suite), then git commit the changes to requirements.txt and push to both github and the dokku server.
