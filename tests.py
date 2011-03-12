import unittest
from parser import ParserBase, LxmlParser

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
    
class LxmlParserTests(unittest.TestCase, ParserTestsAbstract):
    parser_class = LxmlParser

if __name__ == '__main__':
    unittest.main()