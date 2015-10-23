import re
from ..utils import get_name


def build_name(serv):
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

    def inject(self, services):
        self.services = {build_name(serv): serv for serv in services}

    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        try:
            # if isn't not already an attribute,
            # look it up and cache it
            value = self.services[name]
            setattr(self, name, value)
            return value
        except KeyError:
            raise AttributeError(name)
