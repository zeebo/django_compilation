class ParserBase(object):
    def __init__(self, content):
        self.content = content
    
    def get_script_files(self):
        raise NotImplementedError
    
    def get_script_inlines(self):
        raise NotImplementedError
    
    def get_style_files(self):
        raise NotImplementedError
    
    def get_style_inlines(self):
        raise NotImplementedError

class LxmlParser(ParserBase):
    _lxml = None
    
    @property
    def lxml(self):
        if self._lxml is None:
            from lxml import html
            from lxml.etree import tostring
            content = '<root>%s</root>' % self.content
            self._lxml = html.fromstring(content)
        return self._lxml