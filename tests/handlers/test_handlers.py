from tests.utils import CompilerTestCase, make_named_files
from tests.exceptions import TestException
from tests.contexts import command_handler, django_settings, modified_popen, open_exception
from compilation.handlers.base import BaseHandler, BaseCompilingHandler, HandlerRegistry
import contextlib

class HandlerAbstract(object):
    def setUp(self):
        self._scripts = HandlerRegistry.scripts.copy()
        self._styles = HandlerRegistry.styles.copy()
    
    def tearDown(self):
        HandlerRegistry.scripts = self._scripts
        HandlerRegistry.styles = self._styles
    
    def test_read_file(self):
        with make_named_files() as temp_file:
            temp_file.write('test')
            temp_file.flush()
            handler = self.handler(temp_file.name, 'file')
            self.assertEqual(handler.content, 'test')
    
    def test_read_content(self):
        handler = self.handler('test', 'content')
        self.assertEqual(handler.content, 'test')
    
    def test_file_outside_media_url(self):
        with django_settings({'MEDIA_URL': '/nope'}):
            self.assertRaises(ValueError, self.handler, '/test/file', 'url')
        
    def test_read_django_url(self):
        with django_settings():
            with make_named_files() as temp_file:
                temp_file.write('test')
                temp_file.flush()
                handler = self.handler('/test%s' % temp_file.name, 'url')
                self.assertEqual(handler.content, 'test')
        
    def test_invalid_mode(self):
        self.assertRaises(ValueError, self.handler, 'invalid', 'invalid')
    
    def test_calls_pre_insert(self):
        class MyHandler(self.handler):
            mime = ''
            category = '' 
            abstract = True #Don't put it in the registry
            def pre_insert(self):
                raise TestException
        
        handler = MyHandler('test', 'content')
        self.assertRaises(TestException, handler.call_pre_insert)
    
    def test_lazy_read(self):
        with make_named_files() as temp_file:
            with open_exception(temp_file.name):
                temp_file.write('test')
                temp_file.flush()
                
                handler = self.handler(temp_file.name, 'file') #No exception yet
                self.assertRaises(TestException, getattr, handler, 'content') #Read when requested
    
    def test_hash(self):
        import hashlib
        import os.path
        handler = self.handler('test', 'content')
        self.assertEqual(hashlib.sha1('test').hexdigest(), handler.hash)
        
        with make_named_files() as temp_file:
            with open_exception(temp_file.name): #Don't allow it to open the file for the hash
                temp_file.write('test')
                temp_file.flush()
                
                handler = self.handler(temp_file.name, 'file')
                self.assertEqual(hashlib.sha1(str(os.path.getmtime(temp_file.name))).hexdigest(), handler.hash)

class TestBaseHandler(CompilerTestCase, HandlerAbstract):
    handler = BaseHandler

class TestBaseCompilingHandler(CompilerTestCase, HandlerAbstract):
    handler = BaseCompilingHandler
    
    def test_command_works(self):
        #this test ties the implementation to os.popen.
        #If this test fails, make sure the implementation of BaseCompilingHandler hasn't changed
        with contextlib.nested(command_handler(BaseCompilingHandler, HandlerRegistry, 'script', 'some_command -some -args -p %s'), modified_popen()) as (TestHandler, _):
            handler = TestHandler('test', 'content')
            try:
                handler.call_pre_insert()
            except TestException, e:
                #Grab the non variable part of the command (pop the last word off)
                command = ' '.join(e.message.split(' ')[:-1])
                self.assertEqual(command, 'some_command -some -args -p')
            else:
                raise TestException('os.popen not called during compiling')