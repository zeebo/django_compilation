from registry import Registry

class BaseHandler(object):
    __metaclass__ = Registry
    
    mime = ''
    category = ''
    
    def __init__(self):
        pass