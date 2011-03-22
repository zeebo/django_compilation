from tests.utils import CompilerTestCase
from tests.contexts import paths_exist, django_settings
from compilation.locators.base import BaseDirectoryLocator
from compilation.locators.locators import DjangoMediaLocator

class TestDjangoMediaLocator(CompilerTestCase):
    def test_file_outside_media_url(self):
        with django_settings({'MEDIA_URL': '/nope'}):
            self.assertEqual(DjangoMediaLocator.locate('/test/file'), [])
        
    def test_file_inside_media_url(self):
        with django_settings({'MEDIA_URL': '/test/', 'MEDIA_ROOT': '/testroot/'}):
            self.assertEqual(DjangoMediaLocator.locate('/test/file'), ['/testroot/file'])

class TestDirectoryLocator(CompilerTestCase):
    def setUp(self):
        class MyDirectoryLocator(BaseDirectoryLocator):
            url_root = '/dir_statics/'
            dir_root = '/usr/home/lol/statics/'
            
            #Don't let it get registered
            @classmethod
            def valid(cls):
                return False
        
        self.locator = MyDirectoryLocator
    
    def test_invalid_url_prefix(self):
        self.assertEqual(self.locator.locate('/not_dir_statics/css/test.css'), [])
    
    def test_valid_url_prefix(self):
        with paths_exist('/usr/home/lol/statics/css/test.css'):
            self.assertEqual(self.locator.locate('/dir_statics/css/test.css'), ['/usr/home/lol/statics/css/test.css'])