#File should never be imported directly. Import the LocatorRegistry object and it will
#find all of the classes defined in this file.

from base import BaseLocator, BaseDirectoryLocator

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
    
    @classmethod
    def valid(cls):
        try:
            from django.conf import settings
            return'django.contrib.staticfiles' in settings.INSTALLED_APPS
        except:
            return False

#Example directory locator for when your files aren't served by django
#
#    class MyDirectoryLocator(BaseDirectoryLocator):
#       url_root = '/statics/'
#       dir_root = '/usr/home/lol/statics/'
#
#would find files in /usr/home/lol/statics/ for urls starting with /statics/
#for example, <a href="/statics/some/css/file.css"> -> /usr/home/lol/statics/some/css/file.css