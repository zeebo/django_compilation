class BaseGenerator(object):
    @classmethod
    def generate(cls, file_path, file_type):
        getattr(cls, 'generate_%s' % file_type)(cls, file_path)

    @classmethod
    def generate_style(cls, file_path):
        pass
    
    @classmethod
    def generate_script(cls, file_path):
        pass

class MediaUrlGenerator(BaseGenerator):
    @classmethod
    def generate_style(cls, file_path):
        pass
    
    @classmethod
    def generate_script(cls, file_path):
        pass

class StaticfilesUrlGenerator(BaseGenerator):
    @classmethod
    def generate_style(cls, file_path):
        pass
    
    @classmethod
    def generate_script(cls, file_path):
        pass