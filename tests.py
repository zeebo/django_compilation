import unittest
from parser import ParserBase, LxmlParser

def combinations(seq):
    from itertools import combinations as comb
    for n in xrange(1, len(seq)+1):
        for item in comb(seq, n):
            yield item

class CombinationsTests(unittest.TestCase):
    def test_empty_seq(self):
        self.assertEqual(list(combinations([])), [])
    
    def test_four_items(self):
        self.assertEqual(set(combinations('abcd')),
                         set(tuple(x) for x in ['a','b','c','d',
                                                'ab','ac','ad','bc','bd','cd',
                                                'bcd','acd','abd','abc',
                                                'abcd']))

class ParserBaseTests(unittest.TestCase):
    def test_create(self):
        _ = ParserBase('')
    def test_not_implemented(self):
        a = ParserBase('')
        self.assertRaises(NotImplementedError, a.get_script_files)
        self.assertRaises(NotImplementedError, a.get_script_inlines)
        self.assertRaises(NotImplementedError, a.get_style_files)
        self.assertRaises(NotImplementedError, a.get_style_inlines)
        self.assertRaises(NotImplementedError, getattr, a, 'tree') #property

class ParserTestsAbstract(object):
    def test_create(self):
        _ = self.parser_class('')
    
    def test_parse_empty(self):
        p = self.parser_class('')
        _ = p.tree
    
    def test_parse_script_html(self):
        links = [
            ("<link type=\"text/javascript\" href=\"/test/hello.js\" />", ('/test/hello.js', 'text/javascript')),
            ("<link type=\"text/coffeescript\" href=\"/test/hello.coffee\" />", ('/test/hello.coffee', 'text/coffeescript')),
            ("<script type=\"text/javascript\" src=\"/test/hello.js\"></script>", ('/test/hello.js', 'text/javascript')),
            ("<script type=\"text/coffeescript\" src=\"/test/hello.coffee\"></script>", ('/test/hello.coffee', 'text/coffeescript')),
        ]
        for combination in combinations(links):
            html = '\n'.join(link for link, src in combination)
            p = self.parser_class(html)
            scripts = p.get_script_files()
            self.assertEqual(sorted(scripts), sorted(src for _, src in combination))
            
    def test_parse_script_inline_html(self):
        srcs = [
            ("<script type=\"text/javascript\">//inline js</script>", ('//inline js', 'text/javascript')),
            ("<script type=\"text/coffeescript\">//inline coffee</script>", ('//inline coffee', 'text/coffeescript')),
            ("<script type=\"text/undefinedscript\">//inline gobbldygook</script>", ('//inline gobbldygook', 'text/undefinedscript')),
        ]
        for combination in combinations(srcs):
            html = '\n'.join(link for link, src in combination)
            p = self.parser_class(html)
            scripts = p.get_script_inlines()
            self.assertEqual(sorted(scripts), sorted(src for _, src in combination))

    def test_parse_style_html(self):
        links = [
            ("<link type=\"text/css\" href=\"/test/hello.css\" />", ('/test/hello.css', 'text/css')),
            ("<link type=\"text/less\" href=\"/test/hello.less\" />", ('/test/hello.less', 'text/less')),
            ("<style type=\"text/css\" src=\"/test/hello.css\" />", ('/test/hello.css', 'text/css')),
            ("<style type=\"text/sass\" src=\"/test/hello.sass\" />", ('/test/hello.sass', 'text/sass')),
        ]
        for combination in combinations(links):
            html = '\n'.join(link for link, src in combination)
            p = self.parser_class(html)
            scripts = p.get_style_files()
            self.assertEqual(sorted(scripts), sorted(src for _, src in combination))
            
    def test_parse_style_inline_html(self):
        srcs = [
            ("<style type=\"text/css\">inline css</style>", ('inline css', 'text/css')),
            ("<style type=\"text/sass\">inline sass</style>", ('inline sass', 'text/sass')),
            ("<style type=\"text/less\">inline less</style>", ('inline less', 'text/less')),
        ]
        for combination in combinations(srcs):
            html = '\n'.join(link for link, src in combination)
            p = self.parser_class(html)
            scripts = p.get_style_inlines()
            self.assertEqual(sorted(scripts), sorted(src for _, src in combination))

    
    
class LxmlParserTests(unittest.TestCase, ParserTestsAbstract):
    parser_class = LxmlParser

if __name__ == '__main__':
    unittest.main()