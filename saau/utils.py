from unittest.mock import patch
from contextlib import contextmanager
from collections import namedtuple
from functools import wraps

import requests
import arcrest.compat
from betamax import Betamax

Res = namedtuple('Res', 'url,headers,read')


def compat(func=None):
    if func:
        return compat_decorator(func)
    else:
        return compat_context()


def compat_decorator(func):
    @wraps(func)
    def wrapper(*args, **kw):
        with compat_context():
            return func(*args, **kw)
    return wrapper


def side_effect(req):
    r = requests.get(
        req.get_full_url(),
        req.headers,
        data=req.data
    )

    return Res(r.url, r.headers, lambda: r.content)


@contextmanager
def compat_context():
    """
    Patches in heavy-duty caching and requests-lib use
    """

    arcrest.compat.sess = requests.Session()
    with patch('arcrest.compat.urllib2.urlopen', side_effect=side_effect):
        with Betamax(arcrest.compat.sess).use_cassette('cache'):
            yield


def get_name(obj):
    try:
        return obj.__name__
    except AttributeError:
        return obj.__class__.__name__
