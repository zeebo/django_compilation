from registry import Registry, LocatorRegistry
import tempfile
import os

class BaseHandler(object):
    __metaclass__ = Registry
    abstract = True
    
    mime = ''
    category = ''
    
    def __init__(self, data, mode):
        if mode not in ['file', 'url', 'content']:
            raise ValueError('Invalid mode')
        
        self._content = None
        self._file_path = None
        getattr(self, 'init_with_%s' % mode)(data)
    
    def init_with_file(self, data):
        self._file_path = data
    
    def init_with_url(self, data):
        """
        Uses the URL to find the media file to be compressed.
        
        Checks all the locators for files, then picks the one with the most
        recent modified time.
        """
        
        paths = []
        for locator in LocatorRegistry.locators:
            paths.extend(locator.locate(data))
        
        if len(paths) == 0:
            raise ValueError('Unable to locate a file for the url (\'%s\').' % data)
        
        #Schwartzian transform. ohh yeahh
        paths.sort(key=lambda path: os.path.getmtime(path))
        
        self._file_path = paths[0]
    
    def init_with_content(self, data):
        self._content = data
    
    def call_pre_insert(self):
        if hasattr(self, 'pre_insert') and callable(self.pre_insert):
            self.pre_insert()
    
    @property
    def content(self):
        if self._content is not None:
            return self._content
        
        if self._file_path is None:
            raise ValueError('No content in this handler and no idea where to get any')
        
        with open(self._file_path) as handle:
            self._content = handle.read()
        
        return self._content
    
    @property
    def hash(self):
        if self._content is None and self._file_path is None:
            raise ValueError('No content in this handler and no idea where to get any')
        
        import hashlib, os.path
        if self._file_path is not None:
            return hashlib.sha1(str(os.path.getmtime(self._file_path))).hexdigest()
        
        return hashlib.sha1(self._content).hexdigest()


class BaseCompilingHandler(BaseHandler):
    abstract = True
    
    mime = ''
    category = ''
    
    command = ''
    
    def pre_insert(self):
        #Put the content into a file
        with tempfile.NamedTemporaryFile(mode='w+b') as temp:
            temp.write(self.content)
            temp.flush()
            
            exec_command = self.command % temp.name
            
            output = os.popen(exec_command).read()
        
        return output

class BaseLocator(object):
    __metaclass__ = LocatorRegistry
    abstract = True
    
    @classmethod
    def locate(cls, url):
        return []
    
    @classmethod
    def valid(cls):
        return True

class DirectoryLocator(BaseLocator):
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

    