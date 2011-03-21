#File should never be imported directly. Import the Registry object and it will
#find all of the classes defined in this file.

from base import BaseHandler, BaseCompilingHandler

class JavascriptHandler(BaseHandler):
    mime = 'text/javascript'
    category = 'script'

class CoffeescriptHandler(BaseCompilingHandler):
    mime = 'text/coffeescript'
    category = 'script'
    command = 'coffee -p %s'
    output_type = 'stdout'

class CSSHandler(BaseHandler):
    mime = 'text/css'
    category = 'style'

class LESSHandler(BaseCompilingHandler):
    mime = 'text/less'
    category = 'style'
    command = 'lessc %s'

class SASSHandler(BaseHandler):
    mime = 'text/sass'
    category = 'style'