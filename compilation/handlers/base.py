import tempfile
import os

class HandlerRegistry(type):
    """
    Metaclass to register all classes with the mime type they handle.
    """
    
    scripts = {}
    styles = {}
    
    def __new__(meta, classname, bases, class_dict):
        #If abstract, don't register
        if 'abstract' in class_dict and class_dict['abstract']:
            #assert that we don't have a mime type
            if class_dict['mime'] != '':
                raise NotImplementedError('Abstract base handlers should not define a mime type')
            
            #assert that we don't have a category
            if class_dict['category'] != '':
                raise NotImplementedError('Abstract base handlers should not define a category type')
            
            del class_dict['abstract']
            
            return type.__new__(meta, classname, bases, class_dict)
            
        
        if 'mime' not in class_dict or 'category' not in class_dict:
            raise NotImplementedError('Types must implement mime and category')
        
        if class_dict['category'] not in ['script', 'style']:
            raise NotImplementedError('Category must be script or style')
        
        new_class = type.__new__(meta, classname, bases, class_dict)
         
        if class_dict['category'] == 'script':
            meta.scripts[class_dict['mime']] = new_class
        else:
            meta.styles[class_dict['mime']] = new_class
        
        return new_class
    
    @classmethod
    def delete_handler(self, handler):
        if not hasattr(handler, 'category'):
            #Assume it's a string
            if handler in self.scripts:
                del self.scripts[handler]
            if handler in self.styles:
                del self.styles[handler]
        else:
            if handler.category == 'script':
                del self.scripts[handler.mime]
            if handler.category == 'style':
                del self.styles[handler.mime]
    
    @classmethod
    def script_mimes(self):
        return self.scripts.keys()
    
    @classmethod
    def style_mimes(self):
        return self.styles.keys()

class BaseHandler(object):
    __metaclass__ = HandlerRegistry
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
        
        from compilation.locators.base import LocatorRegistry
        
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
            
            self._content = output

import handlers
