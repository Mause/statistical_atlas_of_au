import sys
import logging
from os.path import exists
from functools import lru_cache
from contextlib import contextmanager
from importlib import invalidate_caches
from importlib.machinery import FileFinder, SourceFileLoader

import lib2to3
from lib2to3.refactor import RefactoringTool, get_fixers_from_package

from . import disable_logging


@lru_cache()
def get_rt():
    with disable_logging():
        fixes = get_fixers_from_package('lib2to3.fixes')
        return RefactoringTool(fixes)


class MyLoader(SourceFileLoader):
    def get_data(self, filename):
        if 'arcrest' not in self.name or 'arcrest.compat' in self.name:
            return super().get_data(filename)

        if filename.endswith('.pyc'):
            raise FileNotFoundError()

        py3 = filename + '.py3'
        if exists(py3):
            with open(py3) as fh:
                return fh.read()

        with open(filename, encoding='utf8') as fh:
            contents = fh.read()

        rt = get_rt()

        contents = rt.refactor_docstring(contents, filename)
        contents = rt.refactor_string(contents, filename)
        contents = str(contents)

        with open(py3, 'w') as fh:
            fh.write(contents)

        return contents


@contextmanager
def with_hook():
    hook = FileFinder.path_hook((MyLoader, ['.py']))
    sys.path_hooks.insert(0, hook)
    sys.path_importer_cache.clear()
    invalidate_caches()
    try:
        yield
    finally:
        sys.path_hooks.remove(hook)

