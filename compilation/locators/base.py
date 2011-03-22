class BaseLocator(object):
    __metaclass__ = LocatorRegistry
    abstract = True
    
    @classmethod
    def locate(cls, url):
        return []
    
    @classmethod
    def valid(cls):
        return True

class BaseDirectoryLocator(BaseLocator):
    abstract = True
    
    @classmethod
    def locate(cls, url):
        import os
        if url.startswith(cls.url_root):
            path = url[len(cls.url_root):]
            file_path = os.path.join(cls.dir_root, path)
            if os.path.exists(file_path):
                return [file_path]
        return []

    @classmethod
    def valid(cls):
        import os.path
        if not hasattr(cls, 'url_root') or not hasattr(cls, 'dir_root'):
            return False
        
        if not os.path.exists(cls.dir_root):
            return False
        
        return True