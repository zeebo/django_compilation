from base import BaseHandler

class JavascriptHandler(BaseHandler):
    mime = 'text/javascript'
    category = 'script'

class CoffeescriptHandler(BaseHandler):
    mime = 'text/coffeescript'
    category = 'script'

class CSSHandler(BaseHandler):
    mime = 'text/css'
    category = 'style'

class LESSHandler(BaseHandler):
    mime = 'text/less'
    category = 'style'

class SASSHandler(BaseHandler):
    mime = 'text/sass'
    category = 'style'