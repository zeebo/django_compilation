from registry import Registry

class BaseHandler(object):
    __metaclass__ = Registry
    
    mime = ''
    category = ''
    
    def __init__(self, data, mode):
        if mode not in ['file', 'url', 'content']:
            raise ValueError('Invalid mode')
        
        getattr(self, 'init_with_%s' % mode)(data)
    
    def init_with_file(self, data):
        with open(data, 'r') as handle:
            self.content = handle.read()
    
    def init_with_url(self, data):
        raise NotImplementedError
    
    def init_with_content(self, data):
        self.content = data
    
    def call_pre_insert(self):
        if hasattr(self, 'pre_insert') and callable(self.pre_insert):
            self.pre_insert()
    