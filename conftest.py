import os
import sys
import warnings

import pytest

from conda.common.compat import PY3
from functools import partial

win_default_shells = ["cmd.exe", "powershell", "git_bash", "cygwin"]
shells = ["bash", "zsh"]

if sys.platform == "win32":
    shells = win_default_shells


def pytest_addoption(parser):
    parser.addoption("--shell", action="append", default=[],
                     help="list of shells to run shell tests on")


def pytest_generate_tests(metafunc):
    if 'shell' in metafunc.fixturenames:
        metafunc.parametrize("shell", metafunc.config.option.shell)


@pytest.fixture()
def suppress_resource_warning():
    '''
Suppress `Unclosed Socket Warning`

It seems urllib3 keeps a socket open to avoid costly recreation costs.

xref: https://github.com/kennethreitz/requests/issues/1882
'''
    if PY3:
        warnings.filterwarnings("ignore", category=ResourceWarning)


tmpdir_in_use = None
def get_tmpdir():
    return tmpdir_in_use
@pytest.fixture(autouse=True)
def set_tmpdir(tmpdir):
    global tmpdir_in_use
    if not tmpdir:
        return tmpdir_in_use
    td = tmpdir.strpath
    # print("Setting testing tmpdir (via CONDA_TEST_TMPDIR) to {}".format(td))
    # I do not think setting env. vars so much is sensible, even in tests.
    # .. to make sure this never gets misconstrued for just the dirname. It
    # is the full path to a tmpdir with additions to it by py.test including
    # the test name.
    assert os.sep in td
    os.environ['CONDA_TEST_TMPDIR'] = td
    tmpdir_in_use = td


# From: https://hackebrot.github.io/pytest-tricks/fixtures_as_class_attributes/
# This allows using pytest fixtures in unittest subclasses, here is how to use it:
#
# @auto_inject_fixtures('tmpdir')
# class Test:
#     def test_foo(self):
#         assert self.tmpdir.isdir()
#
# More importantly, this also works for unittest subclasses:
#
# @auto_inject_fixtures('tmpdir')
# class Test2(unittest.TestCase):
#     def test_foo(self):
#         self.assertTrue(self.tmpdir.isdir())

def _inject(cls, names):
    @pytest.fixture(autouse=True)
    def auto_injector_fixture(self, request):
        for name in names:
            setattr(self, name, request.getfixturevalue(name))

    cls.__auto_injector_fixture = auto_injector_fixture
    return cls


def auto_inject_fixtures(*names):
    return partial(_inject, names=names)
