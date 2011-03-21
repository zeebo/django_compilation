import unittest
import tempfile
import contextlib
from tests.contexts import django_exceptions, django_settings, django_template, open_exception, open_redirector, modified_time, modified_popen, paths_exist, exception_handler, command_handler
from tests.utils import MockNodelist, make_named_files
from tests.exceptions import TestException
from parser import ParserBase, LxmlParser, caching_property, _sentinal
from handlers.registry import Registry
from handlers.base import BaseHandler, BaseCompilingHandler

class CompilerTestCase(unittest.TestCase):
    def assertSortedEqual(self, first, second):
        self.assertEqual(sorted(first), sorted(second))

def combinations(seq):
    from itertools import combinations as comb
    for n in xrange(1, len(seq)+1):
        for item in comb(seq, n):
            yield item

class CombinationsTests(CompilerTestCase):
    def test_empty_seq(self):
        self.assertEqual(list(combinations([])), [])
    
    def test_four_items(self):
        combs = list(combinations('abcd'))
        self.assertEqual(set(combs),
                         set(tuple(x) for x in ['a','b','c','d',
                                                'ab','ac','ad','bc','bd','cd',
                                                'bcd','acd','abd','abc',
                                                'abcd']))
        self.assertEqual(len(combs), 2**4 - 1)

class CachingPropertyTests(CompilerTestCase):
    def test_only_called_once(self):
        class TestClass(object):
            def __init__(self):
                self._value = _sentinal
                self.counter = 0
            
            @caching_property('_value')
            def value(self):
                self.counter += 1
                return 'evaluated'
        
        tester = TestClass()
        self.assertEqual(tester.counter, 0)
        tester.value
        self.assertEqual(tester.counter, 1)
        tester.value
        self.assertEqual(tester.counter, 1)

    def test_caches_none(self):
        class TestClass(object):
            def __init__(self):
                self._value = _sentinal
                self.counter = 0
            
            @caching_property('_value')
            def value(self):
                self.counter += 1
                return None
        
        tester = TestClass()
        self.assertEqual(tester.counter, 0)
        tester.value
        self.assertEqual(tester.counter, 1)
        tester.value
        self.assertEqual(tester.counter, 1)
    
    def test_cache_not_init(self):
        def counter(n = {'n': 0}):
            n['n'] += 1
            return n['n']
        
        class TestClass(object):
            @caching_property('_not_init')
            def value(self):
                return counter()
        
        tester = TestClass()
        self.assertEqual(tester.value, 1)
        self.assertEqual(tester.value, 1)

class ParserBaseTests(CompilerTestCase):
    def test_create(self):
        ParserBase('')
    
    def test_not_implemented(self):
        a = ParserBase('')
        
        #properties
        self.assertRaises(NotImplementedError, getattr, a, 'script_files')
        self.assertRaises(NotImplementedError, getattr, a, 'script_inlines')
        self.assertRaises(NotImplementedError, getattr, a, 'style_files')
        self.assertRaises(NotImplementedError, getattr, a, 'style_inlines')
        self.assertRaises(NotImplementedError, getattr, a, 'styles')
        self.assertRaises(NotImplementedError, getattr, a, 'scripts')
        self.assertRaises(NotImplementedError, getattr, a, 'nodes')
        self.assertRaises(NotImplementedError, getattr, a, 'tree') 

class ParserTestsAbstract(object):
    def check_combinations(self, data, call):
        for combination in combinations(data):
            trial_data = '\n'.join(node for node, _ in combination)
            p = self.parser_class(trial_data)
            returned = getattr(p, call)
            self.assertSortedEqual(returned, (retval for _, retval in combination))
    
    def test_create(self):
        self.parser_class('')
    
    def test_inline_script_not_captured_as_url(self):
        parser = self.parser_class('<script type="text/javascript">Inline</script>')
        self.assertEqual(parser.script_files, [])
        
    def test_inline_style_not_captured_as_url(self):
        parser = self.parser_class('<style type="text/css">Inline</style>')
        self.assertEqual(parser.style_files, [])
    
    def test_invalid_html(self):
        parser = self.parser_class('<this isnt >fhtm <html <<')
        self.check_every_attrib(parser)
    
    def test_parse_script_html(self):
        data = [
            ("<link type=\"text/javascript\" href=\"/test/hello.js\" />", ('/test/hello.js', 'text/javascript')),
            ("<link type=\"text/coffeescript\" href=\"/test/hello.coffee\" />", ('/test/hello.coffee', 'text/coffeescript')),
            ("<script type=\"text/javascript\" src=\"/test/hello.js\"></script>", ('/test/hello.js', 'text/javascript')),
            ("<script type=\"text/coffeescript\" src=\"/test/hello.coffee\"></script>", ('/test/hello.coffee', 'text/coffeescript')),
        ]
        self.check_combinations(data, 'script_files')
            
    def test_parse_script_inline_html(self):
        data = [
            ("<script type=\"text/javascript\">//inline js</script>", ('//inline js', 'text/javascript')),
            ("<script type=\"text/coffeescript\">//inline coffee</script>", ('//inline coffee', 'text/coffeescript')),
            ("<script type=\"text/undefinedscript\">//inline gobbldygook</script>", ('//inline gobbldygook', 'text/undefinedscript')),
        ]
        self.check_combinations(data, 'script_inlines')

    def test_parse_style_html(self):
        data = [
            ("<link type=\"text/css\" href=\"/test/hello.css\" />", ('/test/hello.css', 'text/css')),
            ("<link type=\"text/less\" href=\"/test/hello.less\" />", ('/test/hello.less', 'text/less')),
            ("<style type=\"text/css\" src=\"/test/hello.css\" />", ('/test/hello.css', 'text/css')),
            ("<style type=\"text/sass\" src=\"/test/hello.sass\" />", ('/test/hello.sass', 'text/sass')),
        ]
        self.check_combinations(data, 'style_files')
            
    def test_parse_style_inline_html(self):
        data = [
            ("<style type=\"text/css\">inline css</style>", ('inline css', 'text/css')),
            ("<style type=\"text/sass\">inline sass</style>", ('inline sass', 'text/sass')),
            ("<style type=\"text/less\">inline less</style>", ('inline less', 'text/less')),
        ]
        self.check_combinations(data, 'style_inlines')
    
    def test_parse_empty(self):
        parser = self.parser_class('')
        self.check_every_attrib(parser)
    
    def check_every_attrib(self, parser):
        parser.script_files
        parser.script_inlines
        parser.style_files
        parser.style_inlines
        parser.styles
        parser.scripts
        parser.nodes
        parser.tree

class LxmlParserTests(CompilerTestCase, ParserTestsAbstract):
    parser_class = LxmlParser

class RegistryTests(CompilerTestCase):
    def setUp(self):
        self._scripts = Registry.scripts
        self._styles = Registry.styles
    
    def tearDown(self):
        Registry.scripts = self._scripts
        Registry.styles = self._styles
     
    def make_handler(self, _category='', _mime=''):
        class NewHandler(object):
            __metaclass__ = Registry
            category = _category
            mime = _mime
        return NewHandler
    
    def test_abstract_handler(self):
        def make_abstract_handler(_mime=''):
            class TestAbstractHandler(object):
                __metaclass__ = Registry
                category = 'abstract'
                mime = _mime
        
        self.assertRaises(NotImplementedError, make_abstract_handler, 'mime')
        
        before_script, before_style = Registry.scripts, Registry.styles
        make_abstract_handler()
        self.assertEqual(before_script, Registry.scripts)
        self.assertEqual(before_style, Registry.styles)
    
    def test_bad_handler(self):
        self.assertRaises(NotImplementedError, self.make_handler)
        self.assertRaises(NotImplementedError, self.make_handler, '', 'mimetype')
        self.assertRaises(NotImplementedError, self.make_handler, 'invalid', 'mimetype')
    
    def test_registered_script(self):
        handler = self.make_handler('script', 'text/test')
        self.assertEqual(Registry.scripts['text/test'], handler)
    
    def test_registered_style(self):
        handler = self.make_handler('style', 'text/test')
        self.assertEqual(Registry.styles['text/test'], handler)
    
    def test_registry_delete_handler(self):
        handler = self.make_handler('script', 'test/mime')
        self.assertTrue('test/mime' in Registry.scripts)
        Registry.delete_handler(handler)
        self.assertTrue('test/mime' not in Registry.scripts)
        
        handler = self.make_handler('style', 'test/mime')
        self.assertTrue('test/mime' in Registry.styles)
        Registry.delete_handler(handler)
        self.assertTrue('test/mime' not in Registry.styles)
    
    def test_registry_delete_by_mime(self):
        handler = self.make_handler('script', 'test/mime')
        self.assertTrue('test/mime' in Registry.scripts)
        Registry.delete_handler('test/mime')
        self.assertTrue('test/mime' not in Registry.scripts)
        
        handler = self.make_handler('style', 'test/mime')
        self.assertTrue('test/mime' in Registry.styles)
        Registry.delete_handler('test/mime')
        self.assertTrue('test/mime' not in Registry.styles)

class TestHandlerAbstract(object):
    def setUp(self):
        self._scripts = Registry.scripts
        self._styles = Registry.styles
    
    def tearDown(self):
        Registry.scripts = self._scripts
        Registry.styles = self._styles

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
            category = 'abstract' #Don't put it in the registry
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

class TestBaseHandler(CompilerTestCase, TestHandlerAbstract):
    handler = BaseHandler

class TestBaseCompilingHandler(CompilerTestCase, TestHandlerAbstract):
    handler = BaseCompilingHandler
    
    def test_command_works(self):
        #this test ties the implementation to os.popen.
        #If this test fails, make sure the implementation of BaseCompilingHandler hasn't changed
        with contextlib.nested(command_handler(BaseCompilingHandler, Registry, 'script', 'some_command -some -args -p %s'), modified_popen()) as (TestHandler, _):
            handler = TestHandler('test', 'content')
            try:
                handler.call_pre_insert()
            except TestException, e:
                #Grab the non variable part of the command (pop the last word off)
                command = ' '.join(e.message.split(' ')[:-1])
                self.assertEqual(command, 'some_command -some -args -p')
            else:
                raise TestException('os.popen not called during compiling')

class TestTemplateTag(CompilerTestCase):
    def local_exception_handler(self, category):
        return exception_handler(BaseHandler, Registry, category)
    
    def basic_context(self):
        return contextlib.nested(django_template(), django_settings({'COMPILER_ROOT':'/'}), django_exceptions(), paths_exist('/css', '/js'))
    
    def test_handlers_created_style_inline(self):
        with contextlib.nested(self.basic_context(), self.local_exception_handler('style')):
            from templatetags.compiler import CompilerNode
            html = "<style type=\"text/test\">testing</style>"
            nodelist = MockNodelist(html)
            
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(TestException, compiler_node.render, None)

    def test_handlers_created_script_inline(self):
        with contextlib.nested(self.basic_context(), self.local_exception_handler('script')):
            from templatetags.compiler import CompilerNode
            html = "<script type=\"text/test\">testing</script>"
            nodelist = MockNodelist(html)
            
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(TestException, compiler_node.render, None)
    
    def test_invalid_mime(self):
        with self.basic_context():
            from templatetags.compiler import CompilerNode
            html = "<script type=\"invalid/mime\">testing</script>"
            nodelist = MockNodelist(html)
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(ValueError, compiler_node.render, None)
    
    def test_bad_settings_no_compiler_root(self):
        with contextlib.nested(django_exceptions(), django_settings()):
            from django.core.exceptions import ImproperlyConfigured
            from templatetags.compiler import CompilerNode
            html = "<script type=\"text/javascript\">testing</script>"
            nodelist = MockNodelist(html)
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(ImproperlyConfigured, compiler_node.render, None)
        
    def test_bad_settings_compiler_root_dne(self):
        with contextlib.nested(django_exceptions(), django_template(), django_settings({'COMPILER_ROOT':'directory/doesnt/exist'})):
            from django.core.exceptions import ImproperlyConfigured
            from templatetags.compiler import CompilerNode
            html = "<script type=\"text/javascript\">testing</script>"
            nodelist = MockNodelist(html)
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(ImproperlyConfigured, compiler_node.render, None)
    
    def test_scripts_inline_compiled(self):
        with tempfile.NamedTemporaryFile(mode='w') as temp_file:
            read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/js' in filename:
                    return temp_file
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = "<script type=\"text/javascript\">inline</script>"
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertEqual(read_handle.read(), 'inline\n')
    
    def test_scripts_file_compiled(self):
        with contextlib.nested(*make_named_files(2)) as (js_file, temp_file):
            js_file.write('file')
            js_file.flush()
            js_read_handle = open(js_file.name, 'r')
            temp_read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/js' in filename:
                    return temp_file
                if 'media/test.js' in filename:
                    return js_read_handle
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), modified_time(), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = "<link type=\"text/javascript\" href=\"/media/test.js\" />"
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertEqual(temp_read_handle.read(), 'file\n')
    
    def test_scripts_compiled(self):
        with contextlib.nested(*make_named_files(2)) as (js_file, temp_file):
            js_file.write('file')
            js_file.flush()
            js_read_handle = open(js_file.name, 'r')
            temp_read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/js' in filename:
                    return temp_file
                if 'media/test.js' in filename:
                    return js_read_handle
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), modified_time(), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = """
                    <link type="text/javascript" href="/media/test.js" />
                    <script type="text/javascript">inline</script>
                """
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertSortedEqual(temp_read_handle.read().strip().split('\n'), ['file', 'inline'])
    
    def test_styles_inline_compiled(self):
        with tempfile.NamedTemporaryFile(mode='w') as temp_file:
            read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/css' in filename:
                    return temp_file
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = "<style type=\"text/css\">inline</style>"
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertEqual(read_handle.read(), 'inline\n')

    def test_styles_file_compiled(self):
        with contextlib.nested(*make_named_files(2)) as (css_file, temp_file):
            css_file.write('file')
            css_file.flush()
            css_read_handle = open(css_file.name, 'r')
            temp_read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/css' in filename:
                    return temp_file
                if 'media/test.css' in filename:
                    return css_read_handle
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), modified_time(), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = "<link type=\"text/css\" href=\"/media/test.css\" />"
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertEqual(temp_read_handle.read(), 'file\n')

    def test_styles_compiled(self):
        with contextlib.nested(*make_named_files(2)) as (css_file, temp_file):
            css_file.write('file')
            css_file.flush()
            css_read_handle = open(css_file.name, 'r')
            temp_read_handle = open(temp_file.name, 'r')
            def temp_opener(filename):
                if 'media/comp/css' in filename:
                    return temp_file
                if 'media/test.css' in filename:
                    return css_read_handle
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), modified_time(), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = """
                    <link type="text/css" href="/media/test.css" />
                    <style type="text/css">inline</style>
                """
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertSortedEqual(temp_read_handle.read().strip().split('\n'), ['file', 'inline'])

    def test_everything_compiled(self):
        with contextlib.nested(*make_named_files(4)) as (css_file, js_file, css_out, js_out):
            css_file.write('cssfile')
            css_file.flush()
            js_file.write('jsfile')
            js_file.flush()
            
            css_read_handle = open(css_file.name, 'r')
            js_read_handle = open(js_file.name, 'r')
            
            css_out_handle = open(css_out.name, 'r')
            js_out_handle = open(js_out.name, 'r')
            def temp_opener(filename):
                if 'media/comp/css' in filename:
                    return css_out
                if 'media/comp/js' in filename:
                    return js_out
                if 'media/test.css' in filename:
                    return css_read_handle
                if 'media/test.js' in filename:
                    return js_read_handle
                return None
            
            with contextlib.nested(django_exceptions(), django_settings({'COMPILER_ROOT':'comp', 'MEDIA_ROOT':'media', 'MEDIA_URL':'/media/'}), open_redirector(temp_opener), modified_time(), paths_exist('media/comp', 'media/comp/css', 'media/comp/js')):
                from templatetags.compiler import CompilerNode
                html = """
                    <link type="text/css" href="/media/test.css" />
                    <style type="text/css">inline css</style>
                    <link type="text/javascript" href="/media/test.js" />
                    <script type="text/javascript">inline js</script>
                """
                nodelist = MockNodelist(html)
                compiler_node = CompilerNode(nodelist)
                compiler_node.render(None)
                self.assertSortedEqual(css_out_handle.read().strip().split('\n'), ['cssfile', 'inline css'])
                self.assertSortedEqual(js_out_handle.read().strip().split('\n'), ['jsfile', 'inline js'])

if __name__ == '__main__':
    unittest.main()
