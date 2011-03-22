from tests.utils import CompilerTestCase
from compilation.parser.parser import ParserBase, caching_property, _sentinal

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

if __name__ == '__main__':
    unittest.main()