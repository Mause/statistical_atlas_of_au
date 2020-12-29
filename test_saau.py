from saau.loading import load_image_providers, load_service_providers
from saau.__main__ import initialize_providers, Services


def test_load_service_providers():
    services = list(load_service_providers(None))
    services_container = Services()
    assert services
    services = initialize_providers(services, services_container)
    assert services

    services_container.inject(services)
    assert services_container.fonts.get_font()


def test_load_image_providers():
    assert list(load_image_providers(None))
