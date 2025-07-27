PY = python
PIP = $(PY) -m pip

# Install dependencies.

install-prod:
	$(PIP) install -r requirements.txt

install-dev: install-prod
	$(PIP) install -r requirements_dev.txt


# Run migrations.

migrate-prod:
	$(PY) manage.py migrate --settings=ecommerce_project.settings.common

migrate-dev:
	$(PY) manage.py migrate --settings=ecommerce_project.settings.dev



# Start server.

run-prod:
	$(PY) manage.py runserver --settings=ecommerce_project.settings.prod

run-dev:
	$(PY) manage.py runserver --settings=ecommerce_project.settings.dev



dev: install-dev migrate-dev run-dev
prod: install-prod migrate-prod run-prod
