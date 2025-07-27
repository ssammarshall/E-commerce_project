from .common import *

# Application definition
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

DEBUG = True

ROOT_URLCONF = 'ecommerce_project.urls.dev'
