from handlers.registry import Registry
from functools import wraps

def caching_property(attribute):
    def new_decorator(function):
        @property
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            if getattr(self, attribute) is not None:
                return getattr(self, attribute)
            ret_val = function(self, *args, **kwargs)
            setattr(self, attribute, ret_val)
            return ret_val
        return wrapper
    return new_decorator

class ParserBase(object):
    def __init__(self, content):
        self.content = content
        self._tree = None
        self._script_files = None
        self._style_files = None
        self._script_inlines = None
        self._style_inlines = None
        self._styles = None
        self._scripts = None
        self._nodes = None
    
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

class LxmlParser(ParserBase):
    @property
    def tree(self):
        if self._tree is None:
            from lxml import html
            from lxml.etree import tostring
            content = '<root>%s</root>' % self.content
            self._tree = html.fromstring(content)
        return self._tree
    
    @caching_property('_script_files')
    def script_files(self):
        """
        Gets script files (hrefs) from two types of tags and return a list
        of tuples of (src, type)
        """
        script_nodes = self.tree.xpath('script[@src]')
        link_paths = ['link[@type="%s"]' % mime for mime in Registry.script_mimes()]
        link_nodes = self.tree.xpath('|'.join(link_paths))
        return [(node.attrib['src'], node.attrib['type']) for node in script_nodes] + \
               [(node.attrib['href'], node.attrib['type']) for node in link_nodes]
    
    @caching_property('_script_inlines')
    def script_inlines(self):
        """
        Gets script data (srcs) from script tags and return a list
        of tuples of (src, type)
        """
        
        script_nodes = self.tree.findall('script')
        return [(node.text, node.attrib['type']) for node in script_nodes if len(node.text) > 0]
    
    @caching_property('_style_files')
    def style_files(self):
        """
        Gets style files (hrefs) from two types of tags and return a list
        of tuples of (src, type)
        """
        
        style_nodes = self.tree.xpath('style[@src]')
        link_paths = ['link[@type="%s"]' % mime for mime in Registry.style_mimes()]
        link_nodes = self.tree.xpath('|'.join(link_paths))
        return [(node.attrib['src'], node.attrib['type']) for node in style_nodes] + \
               [(node.attrib['href'], node.attrib['type']) for node in link_nodes]
    
    @caching_property('_style_inlines')
    def style_inlines(self):
        """
        Gets style data (srcs) from style tags and return a list
        of tuples of (src, type)
        """
        
        style_nodes = self.tree.findall('style')
        return [(node.text, node.attrib['type']) for node in style_nodes if len(node.text) > 0]
