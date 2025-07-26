from .common import *

# Application definition
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ecommerce',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'password'
    }
}

DEBUG = True

ROOT_URLCONF = 'ecommerce_project.urls.dev'

SECRET_KEY = 'django-insecure-&(sx-tw=wqhgxlolqwkzxgi72f^@&g(e4)xv_%cc9y^0s5x)kr'
