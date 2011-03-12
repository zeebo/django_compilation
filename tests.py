import unittest
from parser import ParserBase, LxmlParser

class ParserBaseTests(unittest.TestCase):
    def test_create(self):
        _ = ParserBase('')
        

if __name__ == '__main__':
    unittest.main()