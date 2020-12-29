from saau.loading import load_image_providers, load_service_providers


def test_load_service_providers():
    assert list(load_service_providers(None))


def test_load_image_providers():
    assert list(load_image_providers(None))
