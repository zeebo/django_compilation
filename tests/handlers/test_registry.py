from tests.utils import CompilerTestCase
from compilation.handlers.base import HandlerRegistry

class TestHandlerRegistry(CompilerTestCase):
    def setUp(self):
        self._scripts = HandlerRegistry.scripts.copy()
        self._styles = HandlerRegistry.styles.copy()
    
    def tearDown(self):
        HandlerRegistry.scripts = self._scripts
        HandlerRegistry.styles = self._styles
     
    def make_handler(self, _category='', _mime=''):
        class NewHandler(object):
            __metaclass__ = HandlerRegistry
            category = _category
            mime = _mime
        return NewHandler
    
    def test_abstract_handler(self):
        def make_abstract_handler(_category='', _mime=''):
            class TestAbstractHandler(object):
                __metaclass__ = HandlerRegistry
                abstract = True
                category = _category
                mime = _mime
        
        self.assertRaises(NotImplementedError, make_abstract_handler, _mime='mime')
        self.assertRaises(NotImplementedError, make_abstract_handler, _category='category')
        
        before_script, before_style = HandlerRegistry.scripts.copy(), HandlerRegistry.styles.copy()
        make_abstract_handler()
        self.assertEqual(before_script, HandlerRegistry.scripts)
        self.assertEqual(before_style, HandlerRegistry.styles)
    
    def test_bad_handler(self):
        self.assertRaises(NotImplementedError, self.make_handler)
        self.assertRaises(NotImplementedError, self.make_handler, '', 'mimetype')
        self.assertRaises(NotImplementedError, self.make_handler, 'invalid', 'mimetype')
    
    def test_registered_script(self):
        handler = self.make_handler('script', 'text/test')
        self.assertEqual(HandlerRegistry.scripts['text/test'], handler)
    
    def test_registered_style(self):
        handler = self.make_handler('style', 'text/test')
        self.assertEqual(HandlerRegistry.styles['text/test'], handler)
    
    def test_registry_delete_handler(self):
        handler = self.make_handler('script', 'test/mime')
        self.assertTrue('test/mime' in HandlerRegistry.scripts)
        HandlerRegistry.delete_handler(handler)
        self.assertTrue('test/mime' not in HandlerRegistry.scripts)
        
        handler = self.make_handler('style', 'test/mime')
        self.assertTrue('test/mime' in HandlerRegistry.styles)
        HandlerRegistry.delete_handler(handler)
        self.assertTrue('test/mime' not in HandlerRegistry.styles)
    
    def test_registry_delete_by_mime(self):
        handler = self.make_handler('script', 'test/mime')
        self.assertTrue('test/mime' in HandlerRegistry.scripts)
        HandlerRegistry.delete_handler('test/mime')
        self.assertTrue('test/mime' not in HandlerRegistry.scripts)
        
        handler = self.make_handler('style', 'test/mime')
        self.assertTrue('test/mime' in HandlerRegistry.styles)
        HandlerRegistry.delete_handler('test/mime')
        self.assertTrue('test/mime' not in HandlerRegistry.styles)