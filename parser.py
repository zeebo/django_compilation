from handlers.registry import Registry

class ParserBase(object):
    def __init__(self, content):
        self.content = content
        self._tree = None
    
    def get_script_files(self):
        raise NotImplementedError
    
    def get_script_inlines(self):
        raise NotImplementedError
    
    def get_style_files(self):
        raise NotImplementedError
    
    def get_style_inlines(self):
        raise NotImplementedError
    
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
    
    def get_script_files(self):
        """
        Gets script files (hrefs) from two types of tags and return a list
        of tuples of (src, type)
        """
        
        script_nodes = self.tree.findall('script')
        link_paths = ['link[@type="%s"]' % mime for mime in Registry.script_mimes()]
        link_nodes = self.tree.xpath('|'.join(link_paths))
        return [(node.attrib['src'], node.attrib['type']) for node in script_nodes] + \
               [(node.attrib['href'], node.attrib['type']) for node in link_nodes]
    
    def get_script_inlines(self):
        """
        Gets script data (srcs) from script tags and return a list
        of tuples of (src, type)
        """
        
        script_nodes = self.tree.findall('script')
        return [(node.text, node.attrib['type']) for node in script_nodes if len(node.text) > 0]
    
    def get_style_files(self):
        """
        Gets style files (hrefs) from two types of tags and return a list
        of tuples of (src, type)
        """
        
        style_nodes = self.tree.findall('style')
        link_paths = ['link[@type="%s"]' % mime for mime in Registry.style_mimes()]
        link_nodes = self.tree.xpath('|'.join(link_paths))
        return [(node.attrib['src'], node.attrib['type']) for node in style_nodes] + \
               [(node.attrib['href'], node.attrib['type']) for node in link_nodes]
        
    def get_style_inlines(self):
        """
        Gets style data (srcs) from style tags and return a list
        of tuples of (src, type)
        """
        
        style_nodes = self.tree.findall('style')
        return [(node.text, node.attrib['type']) for node in style_nodes if len(node.text) > 0]
