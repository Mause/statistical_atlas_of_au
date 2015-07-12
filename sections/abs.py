from io import BytesIO
from zipfile import ZipFile

import requests


def abs_obtain_data(self, obtain_url, filename):
    r = requests.get(obtain_url)

    with ZipFile(BytesIO(r.content)) as ziper:
        namelist = ziper.namelist()
        namelist = [name for name in namelist if 'Footnotes' not in name]
        data = ziper.read(namelist[0])  # weird api but yeah

    with open(self.data_dir_join(filename), 'wb') as fh:
        fh.write(data)

    return bool(data)
