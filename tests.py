import unittest
import tempfile
import contextlib
from parser import ParserBase, LxmlParser
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

class ParserBaseTests(CompilerTestCase):
    def test_create(self):
        _ = ParserBase('')
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
        _ = self.parser_class('')
    
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
        Registry.scripts = {}
        Registry.styles = {}
        
        class ScriptHandler(object):
            __metaclass__ = Registry
            mime = 'text/javascript'
            category = 'script'
        class StyleHandler(object):
            __metaclass__ = Registry
            mime = 'text/css'
            category = 'style'
        class CoffeeHandler(object):
            __metaclass__ = Registry
            mime = 'text/coffeescript'
            category = 'script'
    
    def tearDown(self):
        Registry.scripts = {}
        Registry.styles = {}
    
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
            mime = 'text/javascript'
            category = 'script'
        
        self.assertEqual(Registry.scripts['text/javascript'], NewHandler)
    
    def test_registered_style(self):
        class NewHandler(object):
            __metaclass__ = Registry
            mime = 'text/css'
            category = 'style'
        
        self.assertEqual(Registry.styles['text/css'], NewHandler)
    
    def test_registry_style_mimes(self):
        self.assertSortedEqual(Registry.style_mimes(), ['text/css'])
    
    def test_registry_script_mimes(self):
        self.assertSortedEqual(Registry.script_mimes(), ['text/javascript', 'text/coffeescript'])
    
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

@contextlib.contextmanager
def django_settings(settings = {}):
    #There be magic here!
    import imp, sys
    
    base_settings = {
        'MEDIA_ROOT': '/',
        'MEDIA_URL': '/test/',
    }
    
    base_settings.update(settings)
    
    #Gonna be hacking on the modules. Make a backup
    module_backup = sys.modules
    
    #Create some fake django modules
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
    sys.modules = module_backup

@contextlib.contextmanager
def django_template():
    import imp, sys
    module_backup = sys.modules
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
    sys.modules = module_backup

@contextlib.contextmanager
def open_exception(file_check):
    import __builtin__
    old_open = __builtin__.open
    
    def raises(filename, *args, **kwargs):
        if filename == file_check:
            raise TestException('Data opened before requested')
        return old_open(filename, *args, **kwargs)
    
    __builtin__.open = raises
    yield
    __builtin__.open = old_open

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
            mime = 'text/css'
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

class TestTemplateTag(CompilerTestCase):
    def setUp(self):
        class MyHandler(BaseHandler):
            mime = 'text/test'
            category = 'style'
            
            def __init__(self, *args, **kwargs):
                raise TestException
        
        self.my_handler = MyHandler
        
        with django_template():
            from templatetags.compiler import CompilerNode
            self.CompilerNode = CompilerNode
    
    def tearDown(self):
        Registry.delete_handler(self.my_handler)
    
    def test_handlers_created_style_inline(self):
        #Could use mocking, decided not to so this test has dependencies        
        html = "<style type=\"text/test\">testing</style>"
        nodelist = MockNodelist(html)
        
        compiler_node = self.CompilerNode(nodelist)
        self.assertRaises(TestException, compiler_node.render, None)

    def test_handlers_created_script_inline(self):
        #Could use mocking, decided not to so this test has dependencies
        class MyHandler(BaseHandler):
            mime = 'text/test'
            category = 'script'
            
            def __init__(self, *args, **kwargs):
                raise TestException
        
        html = "<script type=\"text/test\">testing</script>"
        nodelist = MockNodelist(html)
        
        compiler_node = self.CompilerNode(nodelist)
        self.assertRaises(TestException, compiler_node.render, None)
    
if __name__ == '__main__':
    unittest.main()