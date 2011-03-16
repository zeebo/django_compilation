from django import template

def do_compile(parser, token):
    nodelist = parser.parse(('endcompile',))
    parser.delete_first_token()
    return CompilerNode(nodelist)

class CompilerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        output = self.nodelist.render(context)
        
        #Now that we have the html text, do the logic.
        return output

register = template.Library()
register.tag('compile', do_compile)