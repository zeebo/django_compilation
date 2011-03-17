from django import template

def hash_handlers(handlers):
    import hashlib
    return hashlib.sha1(''.join(handler.hash for handler in handlers)).hexdigest()

def do_compile(parser, token):
    nodelist = parser.parse(('endcompile',))
    parser.delete_first_token()
    return CompilerNode(nodelist)

def convert_to_handlers(inlines, urls, handlers):
    def convert(nodes, handlers, node_type):
        returned = []
        for data, mime in nodes:
            if mime not in handlers:
                raise ValueError('Unknown mime type: %s' % mime)
            handler = handlers[mime](data, node_type)
            returned.append(handler)
        return returned
    
    returned = []
    returned.extend(convert(inlines, handlers, 'content'))
    returned.extend(convert(urls, handlers, 'url'))
    return returned

class CompilerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        html = self.nodelist.render(context)
        #Now that we have the html text, do the logic.
        
        from parser import LxmlParser
        from handlers.registry import Registry
        
        parsed = LxmlParser(html)
        styles = convert_to_handlers(parsed.style_inlines, parsed.style_files, Registry.styles)
        scripts = convert_to_handlers(parsed.script_inlines, parsed.script_files, Registry.scripts)
        
        from django.conf import settings
        required_attrs = ('COMPILER_ROOT', 'MEDIA_ROOT')
        bad_attrs = (attr for attr in required_attrs if not hasattr(settings, attr))
        for bad in bad_attrs:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('No %s found in django settings' % bad)
        
        
        output = []
        
        return html
        
register = template.Library()
register.tag('compile', do_compile)