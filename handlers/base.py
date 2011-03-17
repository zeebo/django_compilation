from registry import Registry

class BaseHandler(object):
    __metaclass__ = Registry
    
    mime = ''
    category = 'abstract'
    
    def __init__(self, data, mode):
        if mode not in ['file', 'url', 'content']:
            raise ValueError('Invalid mode')
        
        self._content = None
        self._file_path = None
        getattr(self, 'init_with_%s' % mode)(data)
    
    def init_with_file(self, data):
        self._file_path = data
    
    def init_with_url(self, data):
        """
        Uses the URL to find the media file to be compressed.
        Should support relative urls that begin with MEDIA_URL
        
        Can't support absolute urls without doing a page grab every time
        or complicated cacheing.
        
        Based on
        https://github.com/mintchaos/django_compressor/blob/master/compressor/base.py
        Compressor.get_filename
        """
        
        from django.conf import settings
        import os
        if not data.startswith(settings.MEDIA_URL):
            raise ValueError('Unable to determine where the file for \'%s\' is located. URL must begin with \'%s\'' % (data, settings.MEDIA_URL))
        
        path = data[len(settings.MEDIA_URL):]
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        self._file_path = file_path
    
    def init_with_content(self, data):
        self._content = data
    
    def call_pre_insert(self):
        if hasattr(self, 'pre_insert') and callable(self.pre_insert):
            self.pre_insert()
    
    @property
    def content(self):
        if self._content is not None:
            return self._content
        
        if self._file_path is None:
            raise ValueError('No content in this handler and no idea where to get any')
        
        with open(self._file_path) as handle:
            self._content = handle.read()
        
        return self._content
    
    @property
    def hash(self):
        if self._content is None and self._file_path is None:
            raise ValueError('No content in this handler and no idea where to get any')
        
        import hashlib, os.path
        if self._file_path is not None:
            return hashlib.sha1(str(os.path.getmtime(self._file_path))).hexdigest()
        
        return hashlib.sha1(self._content).hexdigest()
    