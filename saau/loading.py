import logging
import pkgutil
import importlib
from os.path import dirname, basename
from fnmatch import fnmatch


def load_image_providers(filter_pattern):
    """
    Loads image providing modules in submodules of `sections`.
    Said image providers are declared in an `IMAGES` list variable on the
    submodule of `sections`
    """
    return load_providers(filter_pattern, 'IMAGES', 'saau.sections.')


def load_service_providers(filter_pattern):
    return load_providers(filter_pattern, 'SERVICES', 'saau.services.')


def load_providers(filter_pattern, attr_name, package_name):
    logging.info('Loading packages')

    packages = pkgutil.walk_packages(
        [dirname(__file__)],
        prefix='saau.',
        onerror=logging.error
    )

    packages = [
        loader.find_module(name).load_module()
        for loader, name, _ in packages
        if name.startswith(package_name)
    ]

    top_level = [
        package
        for package in packages
        if (
            package.__name__.count('.') == 2 and
            basename(package.__file__) == '__init__.py'
        )
    ]

    if not filter_pattern:
        matcher = lambda _: True
    else:
        logging.info(
            "Filtering providers by \"%s\"",
            filter_pattern
        )
        matcher = lambda prov: fnmatch(prov, filter_pattern)

    def getter(package):
        try:
            return getattr(package, attr_name)
        except AttributeError:
            raise AttributeError(
                "{} doesn't expose a {} attribute"
                .format(package, attr_name)
            )

    image_providers = [
        (package,) + tuple(image_provider.split('.'))
        for package in top_level
        for image_provider in getter(package)
        if matcher(image_provider)
    ]

    logging.info('Loading image providers')

    yield from load_classes(load_submodules(image_providers))


def load_classes(modules):
    for module, classname in modules:
        try:
            yield getattr(module, classname)
        except AttributeError:
            logging.error(
                "Couldn't load class \"%s\"",
                module.__name__ + '.' + classname
            )


def load_submodules(image_providers):
    for package, submodule, classname in image_providers:
        try:
            yield (
                importlib.import_module('.' + submodule, package.__package__),
                classname
            )
        except ImportError:
            logging.error(
                "Couldn't load module \"%s\"",
                package.__package__ + '.' + submodule
            )
