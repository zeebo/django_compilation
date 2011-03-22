class LocatorRegistry(type):
    """
    Metaclass to register all locator classes.
    """
    
    locators = set([])
    
    def __new__(meta, classname, bases, class_dict):
        new_class = type.__new__(meta, classname, bases, class_dict)
        
        #If abstract, don't register
        if 'abstract' in class_dict and class_dict['abstract']:
            del class_dict['abstract']
            return type.__new__(meta, classname, bases, class_dict)
        
        #check if it calls itself valid
        if not new_class.valid():
            return new_class
        
        meta.locators.add(new_class)
        return new_class
    
    @classmethod
    def delete_locator(self, locator):
        try:
            self.locators.remove(locator)
        except KeyError:
            pass

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

import locators