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

import locators
