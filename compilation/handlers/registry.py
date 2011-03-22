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

#import all the handlers
import handlers