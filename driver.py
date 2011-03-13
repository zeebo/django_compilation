from parser import LxmlParser as parser

html = """
<script type="text/javascript" src="/test/hello.js"></script>
<script type="text/coffeescript" src="/test/hello.coffee"></script>
"""

p = parser(html)
print p.get_script_files()

from handlers.registry import Registry

print Registry.scripts
print Registry.styles