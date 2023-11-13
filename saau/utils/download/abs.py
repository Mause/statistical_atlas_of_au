"""
http://www.ausstats.abs.gov.au/Ausstats/subscriber.nsf/0/5CB0F0C29CC07051CA25791F000F2D3A/$File/12160_local_government_area_structure.zip
https://web.archive.org/web/20141026141936/http://stat.abs.gov.au/itt/r.jsp?api
"""
import sys
from functools import cache

import pandas
from pandasdmx import Request


class ABSException(Exception):
    pass


def introspect(datasetid: str) -> None:
    from rich_dataframe import DataFramePrettify

    dataflow = rq().dataflow(datasetid, use_cache=True)

    for flow_id, flow in dataflow.structure.items():
        for dimension in flow.dimensions:
            enum = dimension.local_representation.enumerated
            if enum:
                prett = DataFramePrettify(
                    pandas.DataFrame(
                        [
                            {
                                "id": code.id,
                                "name": code.name.localized_default(),
                                "description": code.description.localized_default(),
                            }
                            for code in enum
                        ]
                    ),
                )
                prett.table.title = f'{flow_id} : {dimension.id} : {enum.id}'
            else:
                df = pandas.DataFrame(
                        [
                            vars(facet)
                            for facet in dimension.local_representation.non_enumerated
                        ]
                    )
                prett = DataFramePrettify(df)
                prett.table.title = f'{flow_id} : {dimension.id}'
            prett.prettify()
            input()


@cache
def rq():
    return Request("ABS_XML", use_cache=True)


def get_generic_data(
    datasetid,
    and_,
    orParent=None,
    start=None,
    end=None,
    top=None,
    bottom=None,
    series=None,
    format=None,  # "json",
):
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

    assert top is None or isinstance(top, int)
    assert bottom is None or isinstance(bottom, int)

    if isinstance(and_, list):
        and_ = dict(item.split(".") for item in and_)

    res = rq().data(
        datasetid,
        key=and_,
        params={
            "startPeriod": start,
            "endPeriod": end,
            "top": top,
            "bottom": bottom,
            "series": series,
            "format": format,
        },
        use_cache=True,
    )
    return res.to_pandas(attributes="osgd", dtypes_from_dsd=True)


def abs_data_to_dataframe(data, delete_cols=None):
    if exists(data):
        df = pandas.read_json(data)
    else:
        df = pandas.read_parquet(data.replace(".json", ".parquet"))
    if delete_cols:
        df = df.drop(delete_cols)
    return df


def main(argv=sys.argv[1:]):
    introspect(argv[0])


if __name__ == "__main__":
    import coloredlogs
    import logging

    coloredlogs.install(level=logging.INFO)
    main()
