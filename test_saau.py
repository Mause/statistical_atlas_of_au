import sys
from os.path import expanduser
import json
from io import BytesIO
from tempfile import mkdtemp
from pathlib import Path
from saau.__main__ import initialize_providers, Services
from saau.sections.transportation.roads import RoadImageProvider
from saau.loading import load_image_providers, load_service_providers
from urllib.response import addinfourl
from typing import Dict

from pytest import fixture, xfail


@fixture
def services():
    services = list(load_service_providers(None))
    services_container = Services()
    assert services
    services = initialize_providers(services, services_container)
    assert services

    services_container.inject(services)

    return services_container


def test_load_service_providers(services):
    assert services.fonts.get_font()


def test_load_image_providers():
    assert list(load_image_providers(None))


def responder(responses: Dict):
    def internal(request):
        return addinfourl(
            fp=BytesIO(json.dumps(responses[request.full_url]).encode()),
            headers={},
            url=request.full_url,
            code=200,
        )

    return internal


def url(bit: str) -> str:
    url = f"http://services.ga.gov.au/site_7/rest/services/{bit}"
    url += ('&' if '?' in url else '?') + 'f=json'
    return url


@xfail('missing library')
def test_roads(services, snapshot, monkeypatch):
    layers = [
        (12, "Major_Road_Network"),
        (15, "All_Roads"),
    ]

    resps = {
        url(""): {
            "folders": [],
            "services": [{"name": "NM_Transport_Infrastructure", "type": "MapServer"}],
        },
        url("NM_Transport_Infrastructure/MapServer/"): {
            "layers": [
                {"id": layer_id, "name": layer_name} for layer_id, layer_name in layers
            ]
        },
    }

    for layer_id, layer_name in layers:
        resps.update(
            {
                url(f"NM_Transport_Infrastructure/MapServer/{layer_id}/"): {
                    "name": layer_name,
                    "extent": {
                        "xmin": 112.92801250000002,
                        "ymin": -43.58749,
                        "xmax": 153.63280999999995,
                        "ymax": -8.933330000000012,
                        "spatialReference": {"wkid": 4283, "latestWkid": 4283},
                    },
                },
                url(
                    f"NM_Transport_Infrastructure/MapServer/{layer_id}/query?geometry=112.92801250000002%2C-43.58749%2C153.63280999999995%2C-8.933330000000012&inSR=4283&spatialRel=esriSpatialRelIntersects"
                ): {
                    "displayFieldName": "NAME",
                    "fieldAliases": {"name": "NAME"},
                    "geometryType": "esriGeometryPolyline",
                    "spatialReference": {"wkid": 4283, "latestWkid": 4283},
                    "fields": [
                        {
                            "name": "name",
                            "type": "esriFieldTypeString",
                            "alias": "NAME",
                            "length": 60,
                        }
                    ],
                    "features": [
                        {
                            "attributes": {"name": "FOREST ROAD"},
                            "geometry": {
                                "paths": [
                                    [
                                        [146.12118750000002, -34.61399849999998],
                                        [146.12117149999995, -34.614528500000006],
                                        [146.12119099999995, -34.614978500000007],
                                        [146.12131499999998, -34.61571600000002],
                                        [146.12143249999997, -34.616426999999987],
                                        [146.12149099999999, -34.617640499999993],
                                        [146.12150399999996, -34.618038500000011],
                                        [146.12171049999995, -34.618738500000006],
                                        [146.12191150000001, -34.619140000000016],
                                    ]
                                ]
                            },
                        },
                    ],
                },
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", responder(resps))

    sut = RoadImageProvider(Path(mkdtemp()), services)
    assert not sut.has_required_data()

    assert sut.obtain_data()
    snapshot.assert_match(sut.load_json(sut.path))
    assert sut.build_image()
