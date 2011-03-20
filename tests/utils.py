import tempfile

def del_keys(thing, *keys):
    for key in keys:
        if key in thing:
            del thing[key]

class MockNodelist(object):
    def __init__(self, retval):
        self.retval = retval
    def render(self, *args, **kwargs):
        return self.retval

def make_named_files(count = 1):
    files = [func(mode='w') for func in [tempfile.NamedTemporaryFile]*count]
    if count == 1:
        return files[0]
    return files
