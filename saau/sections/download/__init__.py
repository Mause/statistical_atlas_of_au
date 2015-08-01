import humanize
import requests
import logging
from shutil import copyfileobj

IMAGES = []


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
