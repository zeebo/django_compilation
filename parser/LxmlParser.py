from parser import ParserBase, caching_property
from handlers.registry import HandlerRegistry

class LxmlParser(ParserBase):
    @caching_property('_tree')
    def tree(self):
        from lxml import html
        from lxml.etree import tostring
        content = '<root>%s</root>' % self.content
        return html.fromstring(content)
    
    @caching_property('_script_files')
    def script_files(self):
        """
        Gets script files (hrefs) from two types of tags and return a list
        of tuples of (src, type)
        """
        script_nodes = self.tree.xpath('script[@src]')
        link_paths = ['link[@type="%s"]' % mime for mime in HandlerRegistry.script_mimes()]
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
        link_paths = ['link[@type="%s"]' % mime for mime in HandlerRegistry.style_mimes()]
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