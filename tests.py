import unittest
import tempfile
import contextlib
from parser import ParserBase, LxmlParser, caching_property, _sentinal
from handlers.registry import Registry
from handlers.base import BaseHandler

class TestException(Exception):
    pass

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
        parser.script_files
        
    def test_inline_style_not_captured_as_url(self):
        parser = self.parser_class('<style type="text/css">Inline</style>')
        parser.style_files
    
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
        def make_handler(_category='', _mime=''):
            class NewHandler(object):
                __metaclass__ = Registry
                category = _category
                mime = _mime
        
        self.assertRaises(NotImplementedError, make_handler)
        self.assertRaises(NotImplementedError, make_handler, '', 'mimetype')
        self.assertRaises(NotImplementedError, make_handler, 'invalid', 'mimetype')
    
    def test_registered_script(self):
        class NewHandler(object):
            __metaclass__ = Registry
            mime = 'text/test'
            category = 'script'
        
        self.assertEqual(Registry.scripts['text/test'], NewHandler)
    
    def test_registered_style(self):
        class NewHandler(object):
            __metaclass__ = Registry
            mime = 'text/test'
            category = 'style'
        
        self.assertEqual(Registry.styles['text/test'], NewHandler)
    
    def test_registry_delete_handler(self):
        class NewHandler(object):
            __metaclass__ = Registry
            mime = 'test/mime'
            category = 'script'
        self.assertTrue('test/mime' in Registry.scripts)
        Registry.delete_handler(NewHandler)
        self.assertTrue('test/mime' not in Registry.scripts)
        
        class NewHandler(object):
            __metaclass__ = Registry
            mime = 'test/mime'
            category = 'style'
        self.assertTrue('test/mime' in Registry.styles)
        Registry.delete_handler(NewHandler)
        self.assertTrue('test/mime' not in Registry.styles)

def del_keys(thing, *keys):
    for key in keys:
        if key in thing:
            del thing[key]

@contextlib.contextmanager
def django_exceptions():
    import imp, sys
    
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    core = imp.new_module('core')
    exceptions = imp.new_module('exceptions')
    
    class ImproperlyConfigured(Exception):
        pass
    
    exceptions.__dict__.update({'ImproperlyConfigured': ImproperlyConfigured})
    core.__dict__.update({'exceptions': exceptions})
    django.__dict__.update({'core': core})
    
    sys.modules.update({
        'django': django,
        'django.core': core,
        'django.core.exceptions': exceptions
    })
    
    yield
    del_keys(sys.modules, 'django', 'django.core', 'django.core.exceptions')


@contextlib.contextmanager
def django_settings(settings = {}):
    #There be magic here!
    import imp, sys
    
    base_settings = {
        'MEDIA_ROOT': '/',
        'MEDIA_URL': '/test/',
    }
    
    base_settings.update(settings)
    
    #Create some fake django modules
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    conf = imp.new_module('conf')
    
    #Make the settings object and stick it in the conf module
    conf.__dict__.update({
        'settings': type('settings', (object,), base_settings)
    })
    
    #Stick conf in the django module
    django.__dict__.update({'conf': conf})
    
    #Add the modules in directly (they appear as builtin)
    sys.modules.update({
        'django': django,
        'django.conf': conf,
    })
    
    #Ready to test!
    yield
    
    #Context over, reset modules
    del_keys(sys.modules, 'django', 'django.conf')

@contextlib.contextmanager
def django_template():
    #Code to make
    #  from django import template
    #  register = template.Library()
    #  register.tag('compile', do_compile)
    #run without a hitch. Uses a bunch of inline class creations
    import imp, sys
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    
    template = type('template', (object,), {
        'Node': object,
        'Library': classmethod(lambda x: type('tag', (object, ), {
            'tag': classmethod(lambda x, y, z: None)
        }))
    })
    django.__dict__.update({'template':template})
    sys.modules.update({
        'django':django
    })
    yield

    del_keys(sys.modules, 'django')

@contextlib.contextmanager
def open_exception(file_check):
    import __builtin__
    old_open = __builtin__.open
    
    def raises(filename, *args, **kwargs):
        if filename == file_check or (callable(file_check) and file_check(filename)):
            raise TestException('%s attempted to be opened when disallowed' % filename)
        return old_open(filename, *args, **kwargs)
    
    __builtin__.open = raises
    yield
    __builtin__.open = old_open

@contextlib.contextmanager
def open_redirector(handle_maker):
    import __builtin__
    old_open = __builtin__.open
    
    def new_open(filename, *args, **kwargs):
        handle = handle_maker(filename)
        if handle is not None:
            return handle
        return old_open(filename, *args, **kwargs)
    
    __builtin__.open = new_open
    yield
    __builtin__.open = old_open

@contextlib.contextmanager
def modified_time(time = ''):
    import sys
    new_mtime = lambda x: time
    old_mtime = sys.modules['os.path'].getmtime
    sys.modules['os.path'].getmtime = new_mtime
    yield
    sys.modules['os.path'].getmtime = old_mtime

@contextlib.contextmanager
def paths_exist(*paths):
    import sys
    
    old_exists = sys.modules['os.path'].exists
    def new_exists(path):
        if path in paths:
            return True
        return old_exists(path)
    sys.modules['os.path'].exists = new_exists
    yield
    sys.modules['os.path'].exists = old_exists

class TestBaseHandler(CompilerTestCase):
    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode='w') as temp_file:
            temp_file.write('test')
            temp_file.flush()
            handler = BaseHandler(temp_file.name, 'file')
            self.assertEqual(handler.content, 'test')
    
    def test_read_content(self):
        handler = BaseHandler('test', 'content')
        self.assertEqual(handler.content, 'test')
    
    def test_file_outside_media_url(self):
        with django_settings({'MEDIA_URL': '/nope'}):
            self.assertRaises(ValueError, BaseHandler, '/test/file', 'url')
        
    def test_read_django_url(self):
        with django_settings():
            with tempfile.NamedTemporaryFile(mode='w') as temp_file:
                temp_file.write('test')
                temp_file.flush()
                handler = BaseHandler('/test%s' % temp_file.name, 'url')
                self.assertEqual(handler.content, 'test')
        
    def test_invalid_mode(self):
        self.assertRaises(ValueError, BaseHandler, 'invalid', 'invalid')
    
    def test_calls_pre_insert(self):
        class MyHandler(BaseHandler):
            mime = 'text/test'
            category = 'style'
            
            def pre_insert(self):
                raise TestException
        
        handler = MyHandler('test', 'content')
        self.assertRaises(TestException, handler.call_pre_insert)
    
    def test_lazy_read(self):
        with tempfile.NamedTemporaryFile(mode='w') as temp_file:
            with open_exception(temp_file.name):
                temp_file.write('test')
                temp_file.flush()
            
                handler = BaseHandler(temp_file.name, 'file') #No exception yet
                self.assertRaises(TestException, getattr, handler, 'content') #Read when requested
    
    def test_hash(self):
        import hashlib
        import os.path
        handler = BaseHandler('test', 'content')
        self.assertEqual(hashlib.sha1('test').hexdigest(), handler.hash)
        
        with tempfile.NamedTemporaryFile(mode='w') as temp_file:
            with open_exception(temp_file.name): #Don't allow it to open the file for the hash
                temp_file.write('test')
                temp_file.flush()
                
                handler = BaseHandler(temp_file.name, 'file')
                self.assertEqual(hashlib.sha1(str(os.path.getmtime(temp_file.name))).hexdigest(), handler.hash)

class MockNodelist(object):
    def __init__(self, retval):
        self.retval = retval
    def render(self, *args, **kwargs):
        return self.retval

def make_named_files(count = 1):
    files = [func(mode='w') for func in [tempfile.NamedTemporaryFile]*count]
    if count == 1:
        return files[0]
    return files

@contextlib.contextmanager
def exception_handler(_category, _mime='text/test'):
    class MyScriptHandler(BaseHandler):
        mime = _mime
        category = _category
        
        def __init__(self, *args, **kwargs):
            raise TestException
    yield
    Registry.delete_handler(MyScriptHandler)

class TestTemplateTag(CompilerTestCase):
    def basic_context(self):
        return contextlib.nested(django_template(), django_settings({'COMPILER_ROOT':'/'}), django_exceptions(), paths_exist('/css', '/js'))
    
    def test_handlers_created_style_inline(self):
        with contextlib.nested(self.basic_context(), exception_handler('style')):
            from templatetags.compiler import CompilerNode
            html = "<style type=\"text/test\">testing</style>"
            nodelist = MockNodelist(html)
            
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(TestException, compiler_node.render, None)

    def test_handlers_created_script_inline(self):
        with contextlib.nested(self.basic_context(), exception_handler('script')):
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
