from functools import wraps

_sentinal = object()
def caching_property(attribute):
    def new_decorator(function):
        @property
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, attribute) and getattr(self, attribute) is not _sentinal:
                return getattr(self, attribute)
            ret_val = function(self, *args, **kwargs)
            setattr(self, attribute, ret_val)
            return ret_val
        return wrapper
    return new_decorator

class ParserBase(object):
    def __init__(self, content):
        self.content = content
    
    @property
    def script_files(self):
        raise NotImplementedError
    
    @property
    def script_inlines(self):
        raise NotImplementedError
    
    @property
    def style_files(self):
        raise NotImplementedError
    
    @property
    def style_inlines(self):
        raise NotImplementedError
    
    @caching_property('_styles')
    def styles(self):
        return self.style_inlines + self.style_files
    
    @caching_property('_scripts')
    def scripts(self):
        return self.script_inlines + self.script_files
    
    @caching_property('_nodes')
    def nodes(self):
        return self.styles + self.scripts
    
    @property
    def tree(self):
        raise NotImplementedError
