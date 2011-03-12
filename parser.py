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