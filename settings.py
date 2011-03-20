try:
    from django.conf import settings as django_settings
except ImportError:
    django_settings = object()

class PropertyDict(object):
    def __init__(self, data):
        self.update(data)
    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)

COMPILER = PropertyDict({
    'PARSER_CLASS': getattr(django_settings, 'COMPILER_PARSER_CLASS', 'LxmlParser'),
})
