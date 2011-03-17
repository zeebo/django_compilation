from django import template
from parser import LxmlParser
from handlers.registry import Registry
import hashlib

def hash_handlers(handlers):
    return hashlib.sha1(''.join(handler.hash for handler in handlers)).hexdigest()

def do_compile(parser, token):
    nodelist = parser.parse(('endcompile',))
    parser.delete_first_token()
    return CompilerNode(nodelist)

class CompilerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        html = self.nodelist.render(context)
        #Now that we have the html text, do the logic.
        
        parsed = LxmlParser(html)
        styles, scripts = [], []
        for data, mime in parsed.styles:
            node_type = (data, mime) in parsed.style_inlines and 'content' or 'url'
            handler = Registry.styles[mime](data, node_type)
            styles.append(handler)
        
        for data, mime in parsed.scripts:
            node_type = (data, mime) in parsed.script_inlines and 'content' or 'url'
            handler = Registry.scripts[mime](data, node_type)
            scripts.append(handler)
        
        output = []
        
        return html
        
register = template.Library()
register.tag('compile', do_compile)