init:
	pip install pipenv --upgrade
	pipenv install --dev

test:
	pipenv run python manage.py test home/
