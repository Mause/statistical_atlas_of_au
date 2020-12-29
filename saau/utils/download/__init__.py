import humanize
import requests
import logging
from shutil import copyfileobj
from zipfile import ZipFile
from io import BytesIO
from os.path import exists, splitext
from typing import List, Any

IMAGES: List[Any] = []


def get_binary(url, filename):
    r = requests.head(url)

    if 'Content-Length' in r.headers:
        logging.warning(
            '%s is quite large at %s. '
            'Considering downloading it manually?',
            url,
            humanize.naturalsize(int(r.headers['Content-Length']))
        )

    r = requests.get(url, stream=True)

    with open(filename, 'wb') as fh:
        copyfileobj(
            r.raw,
            fh
        )

    return True


def get_abs_csv(url, filename):
    r = requests.get(url)
    assert r.ok, r.json()
    content = r.content

    assert splitext(filename)[1] == '.csv'

    with ZipFile(BytesIO(content)) as ziper:
        data = ziper.read(ziper.namelist()[0])

    with open(filename, 'wb') as fh:
        fh.write(data)

    return exists(filename)
