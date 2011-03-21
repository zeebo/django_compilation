import contextlib
from utils import del_keys
from exceptions import TestException


@contextlib.contextmanager
def django_exceptions():
    import imp, sys
    
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    core = imp.new_module('core')
    exceptions = imp.new_module('exceptions')
    
    class ImproperlyConfigured(Exception):
        pass
    
    exceptions.__dict__.update({'ImproperlyConfigured': ImproperlyConfigured})
    core.__dict__.update({'exceptions': exceptions})
    django.__dict__.update({'core': core})
    
    sys.modules.update({
        'django': django,
        'django.core': core,
        'django.core.exceptions': exceptions
    })
    
    yield
    del_keys(sys.modules, 'django', 'django.core', 'django.core.exceptions')

@contextlib.contextmanager
def django_settings(settings = {}):
    #There be magic here!
    import imp, sys
    
    base_settings = {
        'MEDIA_ROOT': '/',
        'MEDIA_URL': '/test/',
    }
    
    base_settings.update(settings)
    
    #Create some fake django modules
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    conf = imp.new_module('conf')
    
    #Make the settings object and stick it in the conf module
    conf.__dict__.update({
        'settings': type('settings', (object,), base_settings)
    })
    
    #Stick conf in the django module
    django.__dict__.update({'conf': conf})
    
    #Add the modules in directly (they appear as builtin)
    sys.modules.update({
        'django': django,
        'django.conf': conf,
    })
    
    #Ready to test!
    yield
    
    #Context over, reset modules
    del_keys(sys.modules, 'django', 'django.conf')

@contextlib.contextmanager
def django_template():
    #Code to make
    #  from django import template
    #  register = template.Library()
    #  register.tag('compile', do_compile)
    #run without a hitch. Uses a bunch of inline class creations
    import imp, sys
    if 'django' in sys.modules:
        django = sys.modules['django']
    else:
        django = imp.new_module('django')
    
    template = type('template', (object,), {
        'Node': object,
        'Library': classmethod(lambda x: type('tag', (object, ), {
            'tag': classmethod(lambda x, y, z: None)
        }))
    })
    django.__dict__.update({'template':template})
    sys.modules.update({
        'django':django
    })
    yield

    del_keys(sys.modules, 'django')

@contextlib.contextmanager
def open_exception(file_check):
    import __builtin__
    old_open = __builtin__.open
    
    def raises(filename, *args, **kwargs):
        if filename == file_check or (callable(file_check) and file_check(filename)):
            raise TestException('%s attempted to be opened when disallowed' % filename)
        return old_open(filename, *args, **kwargs)
    
    __builtin__.open = raises
    yield
    __builtin__.open = old_open

@contextlib.contextmanager
def open_redirector(handle_maker):
    import __builtin__
    old_open = __builtin__.open
    
    def new_open(filename, *args, **kwargs):
        handle = handle_maker(filename)
        if handle is not None:
            return handle
        return old_open(filename, *args, **kwargs)
    
    __builtin__.open = new_open
    yield
    __builtin__.open = old_open

@contextlib.contextmanager
def modified_time(time = ''):
    import sys
    new_mtime = lambda x: time
    old_mtime = sys.modules['os.path'].getmtime
    sys.modules['os.path'].getmtime = new_mtime
    yield
    sys.modules['os.path'].getmtime = old_mtime

@contextlib.contextmanager
def modified_popen():
    import sys
    def new_popen(command):
        raise TestException(command)
    old_popen = sys.modules['os'].popen
    sys.modules['os'].popen = new_popen
    yield
    sys.modules['os'].popen = old_popen


@contextlib.contextmanager
def command_handler(cls, regis, _category, _command, _mime='text/test'):
    class TestHandler(cls):
        mime = _mime
        category = _category
        command = _command
    yield TestHandler
    regis.delete_handler(TestHandler)


@contextlib.contextmanager
def paths_exist(*paths):
    import sys
    
    old_exists = sys.modules['os.path'].exists
    def new_exists(path):
        if path in paths:
            return True
        return old_exists(path)
    sys.modules['os.path'].exists = new_exists
    yield
    sys.modules['os.path'].exists = old_exists

@contextlib.contextmanager
def exception_handler(cls, regis, _category, _mime='text/test'):
    class MyScriptHandler(cls):
        mime = _mime
        category = _category
        
        def __init__(self, *args, **kwargs):
            raise TestException
    yield
    regis.delete_handler(MyScriptHandler)