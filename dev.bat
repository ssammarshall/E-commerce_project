@echo off

python -m pip install -r requirements_dev.txt
python manage.py migrate --settings=ecommerce_project.settings.dev
python manage.py runserver --settings=ecommerce_project.settings.dev
