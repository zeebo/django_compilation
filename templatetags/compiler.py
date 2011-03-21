from django import template
from settings import COMPILER

def hash_handlers(handlers):
    import hashlib
    return hashlib.sha1(''.join(handler.hash for handler in handlers)).hexdigest()

def do_compile(parser, token):
    nodelist = parser.parse(('endcompile',))
    parser.delete_first_token()
    return CompilerNode(nodelist)

def convert_to_handlers(inlines, urls, handlers):
    def convert(nodes, node_type):
        returned = []
        for data, mime in nodes:
            if mime not in handlers:
                raise ValueError('Unknown mime type: %s' % mime)
            handler = handlers[mime](data, node_type)
            returned.append(handler)
        return returned
    
    returned = []
    returned.extend(convert(inlines, 'content'))
    returned.extend(convert(urls, 'url'))
    return returned

def get_html_tag(handlers, node_type):
    from django.conf import settings
    import os.path
    
    #Some convenience lookup dictionaries
    extension = {
        'script': 'js',
        'style': 'css',
    }
    mime = {
        'script': 'text/javascript',
        'style': 'text/css'
    }
    
    #no tag if there arent any nodes
    if len(handlers) == 0:
        return ''
    
    directory = os.path.join(settings.MEDIA_ROOT, settings.COMPILER_ROOT, extension[node_type])
    filename = '%s.%s' % (hash_handlers(handlers), extension[node_type])
    url = os.path.join(settings.MEDIA_URL, extension[node_type], filename) #TODO: change to url_generators
    full_path = os.path.join(directory, filename)
    
    if not os.path.exists(full_path):
        #Need to make the file
        with open(full_path, 'w') as file_handle:
            for handler in handlers:
                handler.call_pre_insert()
                file_handle.write(handler.content)
                file_handle.write('\n')
            file_handle.flush()
    
    return '<link type=\'%s\' href=\'%s\' />' % (mime[node_type], url)

class CompilerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        #First check if the environment is set up right
        from django.conf import settings
        required_attrs = ('COMPILER_ROOT', 'MEDIA_ROOT', 'MEDIA_URL')
        bad_attrs = (attr for attr in required_attrs if not hasattr(settings, attr))
        for bad in bad_attrs:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('No %s found in django settings' % bad)
        
        #Check if the directories exist
        import os.path
        directory = os.path.join(settings.MEDIA_ROOT, settings.COMPILER_ROOT)
        required_dirs = (directory, os.path.join(directory, 'css'), os.path.join(directory, 'js'))
        bad_dirs = (d for d in required_dirs if not os.path.exists(d))
        for d in bad_dirs:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('COMPILER_ROOT directory not found. (%s)' % d)
        
        from handlers.registry import Registry
        try:
            import parser
            Parser = getattr(parser, COMPILER.PARSER_CLASS)
        except AttributeError, ImportError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('Unable to import PARSER_CLASS (parser.%s)' % PARSER_CLASS)
        
        html = self.nodelist.render(context)
        parsed = Parser(html)
        styles = convert_to_handlers(parsed.style_inlines, parsed.style_files, Registry.styles)
        scripts = convert_to_handlers(parsed.script_inlines, parsed.script_files, Registry.scripts)
        
        output = []
        output.append(get_html_tag(scripts, 'script'))
        output.append(get_html_tag(styles, 'style'))
        
        return '\n'.join(output)
        
register = template.Library()
register.tag('compile', do_compile)
