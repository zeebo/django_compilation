from django import template
from parser import LxmlParser
from handlers.registry import Registry

def do_compile(parser, token):
    nodelist = parser.parse(('endcompile',))
    parser.delete_first_token()
    return CompilerNode(nodelist)

class CompilerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        output = self.nodelist.render(context)
        #Now that we have the html text, do the logic.
        
        parsed = LxmlParser(output)
        for data, mime in parsed.get_style_inlines():
            handler = Registry.styles[mime](data, 'inline')
            print handler.hash
        
        return output

register = template.Library()
register.tag('compile', do_compile)