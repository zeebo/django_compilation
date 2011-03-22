from tests.utils import CompilerTestCase, MockNodelist, make_named_files
from tests.contexts import django_exceptions, django_template, django_settings, paths_exist, open_redirector, modified_time, exception_handler
from tests.exceptions import TestException
import tempfile
import contextlib

class TestTemplateTag(CompilerTestCase):
    def local_exception_handler(self, category):
        from compilation.handlers.base import BaseHandler, HandlerRegistry
        return exception_handler(BaseHandler, HandlerRegistry, category)
    
    def basic_context(self):
        return contextlib.nested(django_template(), django_settings({'COMPILER_ROOT':'/'}), django_exceptions(), paths_exist('/css', '/js'))
    
    def test_handlers_created_style_inline(self):
        with contextlib.nested(self.basic_context(), self.local_exception_handler('style')):
            from compilation.templatetags.compiler import CompilerNode
            html = "<style type=\"text/test\">testing</style>"
            nodelist = MockNodelist(html)
            
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(TestException, compiler_node.render, None)

    def test_handlers_created_script_inline(self):
        with contextlib.nested(self.basic_context(), self.local_exception_handler('script')):
            from compilation.templatetags.compiler import CompilerNode
            html = "<script type=\"text/test\">testing</script>"
            nodelist = MockNodelist(html)
            
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(TestException, compiler_node.render, None)
    
    def test_invalid_mime(self):
        with self.basic_context():
            from compilation.templatetags.compiler import CompilerNode
            html = "<script type=\"invalid/mime\">testing</script>"
            nodelist = MockNodelist(html)
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(ValueError, compiler_node.render, None)
    
    def test_bad_settings_no_compiler_root(self):
        with contextlib.nested(django_exceptions(), django_settings()):
            from django.core.exceptions import ImproperlyConfigured
            from compilation.templatetags.compiler import CompilerNode
            html = "<script type=\"text/javascript\">testing</script>"
            nodelist = MockNodelist(html)
            compiler_node = CompilerNode(nodelist)
            self.assertRaises(ImproperlyConfigured, compiler_node.render, None)
        
    def test_bad_settings_compiler_root_dne(self):
        with contextlib.nested(django_exceptions(), django_template(), django_settings({'COMPILER_ROOT':'directory/doesnt/exist'})):
            from django.core.exceptions import ImproperlyConfigured
            from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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
                from compilation.templatetags.compiler import CompilerNode
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