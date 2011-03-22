from tests.utils import CompilerTestCase
from test_parser import ParserTestsAbstract
from compilation.parser.LxmlParser import LxmlParser

class LxmlParserTests(CompilerTestCase, ParserTestsAbstract):
    parser_class = LxmlParser
