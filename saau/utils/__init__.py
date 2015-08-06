from unittest.mock import patch
from contextlib import contextmanager
from collections import namedtuple
from functools import wraps
from glob import iglob as glob
from os.path import splitext
import os

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


def move_old(filename):
    def get_rest(related):
        for rel in related:
            try:
                yield int(
                    rel.split('.')[-2]
                )
            except ValueError:
                pass

    name, ext = splitext(filename)
    related = max(
        get_rest(glob(name + '*')) or [],
        default=0
    )
    os.rename(
        filename,
        '{}.{}{}'.format(
            name,
            related + 1,
            ext
        )
    )
