from debug_toolbar.toolbar import debug_toolbar_urls
from .common import *

urlpatterns += debug_toolbar_urls()
