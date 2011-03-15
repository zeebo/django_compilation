class Registry(type):
    """
    Metaclass to register all classes with the mime type they handle.
    """
    
    scripts = {}
    styles = {}
    
    def __new__(meta, classname, bases, class_dict):
        new_class = type.__new__(meta, classname, bases, class_dict)
        
        if 'mime' not in class_dict or 'category' not in class_dict:
            raise NotImplementedError('Types must implement mime and category')
        
        if class_dict['category'] not in ['script', 'style', 'abstract']:
            raise NotImplementedError('Category must be script or style')
        
        #If abstract, don't register
        if class_dict['category'] == 'abstract':
            #assert that we don't have a mime type
            if class_dict['mime'] != '':
                raise NotImplementedError('Abstract base handlers should not define a mime type')
            
            return new_class
        
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

#import all the handlers
import handlers