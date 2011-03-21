#File should never be imported directly. Import the LocatorRegistry object and it will
#find all of the classes defined in this file.

from base import BaseLocator

class DjangoMediaLocator(BaseLocator):
    @classmethod
    def locate(cls, url):
        from django.conf import settings
        import os
        if url.startswith(settings.MEDIA_URL):
            path = url[len(settings.MEDIA_URL):]
            file_path = os.path.join(settings.MEDIA_ROOT, path)
            return [file_path]
        return []

class DjangoStaticfilesLocator(BaseLocator):
    @classmethod
    def locate(cls, url):
        from django.conf import settings
        if 'django.contrib.staticfiles' not in settings.INSTALLED_APPS:
            return []
        
        from django.contrib.staticfiles import finders
        if url.startswith(settings.STATIC_URL):
            path = url[len(settings.STATIC_URL):]
            return finders.find(path)
        return []
    
    @property
    @classmethod
    def valid(cls):
        from django.conf import settings
        return'django.contrib.staticfiles' in settings.INSTALLED_APPS
