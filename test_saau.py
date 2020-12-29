from saau.loading import load_image_providers, load_service_providers


def test_load_service_providers():
    assert load_service_providers(None)


def test_load_image_providers():
    assert load_image_providers(None)