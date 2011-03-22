from tests.utils import CompilerTestCase
from compilation.locators.base import LocatorRegistry

class LocatorRegistryTests(CompilerTestCase):
    def setUp(self):
        self._locators = LocatorRegistry.locators.copy()
    
    def tearDown(self):
        LocatorRegistry.locators = self._locators
    
    def make_locator(self, _abstract = False):
        class NewLocator(object):
            __metaclass__ = LocatorRegistry
            abstract = _abstract
        return NewLocator
    
    def test_abstract_locator(self):
        before_locators = LocatorRegistry.locators.copy()
        self.make_locator(_abstract = True)
        self.assertSortedEqual(before_locators, LocatorRegistry.locators)
    
    def test_invalid_locator_not_registered(self):
        before_locators = LocatorRegistry.locators.copy()
        
        class NewLocator(object):
            __metaclass__ = LocatorRegistry
            
            @classmethod
            def valid(cls):
                return False
        
        self.assertSortedEqual(before_locators, LocatorRegistry.locators)