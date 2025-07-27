$ErrorActionPreference = 'Stop'

python -m pip install -r requirements_prod.txt
python manage.py migrate --settings=ecommerce_project.settings.common
python manage.py runserver --settings=ecommerce_project.settings.prod
