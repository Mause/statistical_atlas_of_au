import re
from ..utils import get_name
from typing import Any, Dict


def build_name(serv):
    """
    Determines a name for a service.

    If it already has a `service_name` attribute, use that, otherwise
    convert the class name to dead-snake case.
    """
    if hasattr(serv, 'service_name'):
        return serv.service_name

    return re.sub(
        r'([A-Z][a-z])',
        lambda m: '_' + m.group(0).lower(),
        get_name(serv)
    ).lower().strip('_')


class Services:
    __str__ = __repr__ = lambda self: (
        '<Services times {}>'.format(len(self.services))
    )

    services: Dict[str, Any]

    def inject(self, services):
        self.services = {build_name(serv): serv for serv in services}

    def __getattr__(self, name):
        try:
            # if it's not already an attribute,
            # look it up and cache it
            value = self.services[name]
            setattr(self, name, value)
            return value
        except KeyError:
            raise AttributeError(name)
