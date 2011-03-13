class Registry(type):
    scripts = {}
    styles = {}
    
    def __new__(meta, classname, bases, class_dict):
        new_class = type.__new__(meta, classname, bases, class_dict)
        
        #Check for the base class and ignore it
        if classname == 'BaseHandler':
            return new_class
        
        if 'mime' not in class_dict or 'category' not in class_dict:
            raise NotImplementedError('Types must implement mime and category')
        
        if class_dict['category'] not in ['script', 'style']:
            raise NotImplementedError('Category must be script or style')
        
        if class_dict['category'] == 'script':
            meta.scripts[class_dict['mime']] = new_class
        else:
            meta.styles[class_dict['mime']] = new_class
        
        return new_class
    
    @classmethod
    def script_mimes(self):
        return self.scripts.keys()
    
    @classmethod
    def style_mimes(self):
        return self.styles.keys()

from handlers import *