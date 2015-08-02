"""
http://www.ausstats.abs.gov.au/Ausstats/subscriber.nsf/0/5CB0F0C29CC07051CA25791F000F2D3A/$File/12160_local_government_area_structure.zip
https://web.archive.org/web/20141026141936/http://stat.abs.gov.au/itt/r.jsp?api
"""

from io import BytesIO
from zipfile import ZipFile

import pandas
import requests

BASE = 'http://stat.abs.gov.au/itt/query.jsp'
NoneType = type(None)


class ABSException(Exception):
    pass


def abs_obtain_data(self, obtain_url, filename):
    r = requests.get(obtain_url)

    with ZipFile(BytesIO(r.content)) as ziper:
        namelist = ziper.namelist()
        namelist = [name for name in namelist if 'Footnotes' not in name]
        data = ziper.read(namelist[0])  # weird api but yeah

    with open(self.data_dir_join(filename), 'wb') as fh:
        fh.write(data)

    return bool(data)


def query(method, params):
    params.update({
        'method': method,
        'format': 'json'
    })
    datum = requests.get(
        BASE,
        params=params
    ).json()

    if 'exception' in datum:
        raise ABSException(datum['exception'])

    return datum


def introspect(datasetid):
    concepts = get_dataset_concepts(datasetid)
    assert 'concepts' in concepts, concepts
    concepts = concepts['concepts']

    for concept in concepts:
        codes = get_codelist_value(datasetid, concept)['codes']
        print(concept, '->', ', '.join(
            '[{description}:{code}]'.format_map(code)
            for code in codes
        ))
        input()


def get_dataset_list():
    return query('GetDatasetList', {})


def get_dataset_concepts(datasetid):
    return query('GetDatasetConcepts', {'datasetid': datasetid})


def get_codelist_value(datasetid, concept, code=None, relationship=None):
    assert concept.isupper(), 'Concepts are case sensitive'
    if relationship is not None:
        assert relationship in {
            'parent',
            'children',
            'parentCode'
        }
    if code and isinstance(code, str):
        code = [code]

    return query(
        'GetCodeListValue',
        {
            'datasetid': datasetid,
            'concept': concept,
            'relationship': relationship,
            'code': code
        }
    )


commas = ','.join


def get_generic_data(datasetid, and_, or_=None, orParent=None, start=None,
                     end=None, top=None, bottom=None, series=None,
                     format='json'):
    """
    :param datasetid: Any dataset ID in ABS.Stat. These can be retrieved using
                      the GetDatasetList method.
                      Note: Case sensitive    LF, CPI, ABS_CENSUS2011_B01
    :param and: A list of comma separated concepts and values for the and and
                part of the query. The format is CONCEPT.VALUE.
                &and=ASGC_2010.0
    :param or:  A list of comma separated concepts and values for the or and
                part of the query. The format is CONCEPT.VALUE.
                &or=ASGS.1
    :param orParent: A code in the format CONCEPT.VALUE.
                     Uses all children of the specified code for the query.
                     &orParent=ASGC_2010.0
                     All codes with the parent ASGC_2010.0 (Australia) are
                     selected. Data for all states would be returned.
    :param start: Start date in the appropriate format
                  &start=2006 : Annual data
                  &start=2006-Q3 : Quarterly data
                  &start=2006-11 : Monthly data
    :param end: End date in the appropriate format
                &end=2006
    :param top: Integer. Returns a sorted list of the top N results.
                &top=10
                &top=-1 will return all results in a sorted list.
    :param bottom: Integer. Returns a sorted list of the bottom N results.
                   &bottom=10
                   &bottom=-1 will return all results in a sorted list.
    :param series: latest or years
                   &series=latest : Returns values from the latest series in
                   the dataset.
                   &series=2009,2010,2005 : Returns values for 2005,2009 and
                   2010
    :param format: see elsewhere
    """

    assert isinstance(top, (NoneType, int))
    assert isinstance(bottom, (NoneType, int))

    assert isinstance(format, str)
    assert format in {
        'csv',
        'htable',
        'vtable',
        'json',
        'latest',
        'excel'
    }

    if isinstance(and_, list):
        and_ = commas(and_)

    if isinstance(or_, list):
        or_ = commas(or_)

    return query(
        'GetGenericData',
        {
            'datasetid': datasetid,
            'and': and_,
            'or': or_,
            'orParent': orParent,
            'start': start,
            'end': end,
            'top': top,
            'bottom': bottom,
            'series': series,
            'format': format
        }
    )


def collapse_concepts(concepts):
    return {t['name']: t['Value'] for t in concepts}


def abs_data_to_dataframe(data):
    data = [
        dict(
            collapse_concepts(locale['concepts']),
            **observation
        )
        for locale in data['series']
        for observation in locale['observations']
    ]

    return pandas.DataFrame(data).convert_objects(convert_numeric=True)


if __name__ == '__main__':
    import sys
    introspect(sys.argv[1])
