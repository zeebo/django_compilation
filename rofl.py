import unittest
import tempfile
import contextlib
from tests.contexts import django_exceptions, django_settings, django_template, open_exception, open_redirector, modified_time, modified_popen, paths_exist, exception_handler, command_handler, django_staticfiles
from tests.utils import MockNodelist, make_named_files
from tests.exceptions import TestException
from parser import ParserBase, LxmlParser, caching_property, _sentinal
from handlers.registry import Registry, LocatorRegistry
from handlers.base import BaseHandler, BaseCompilingHandler, BaseDirectoryLocator
from handlers.locators import DjangoMediaLocator


if __name__ == '__main__':
    unittest.main()
