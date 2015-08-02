import re

def build_name(serv):
    if hasattr(serv, 'service_name'):
        return serv.service_name

    return re.sub(
        r'([A-Z][a-z])',
        lambda m: '_' + m.group(0).lower(),
        get_name(serv)
    ).lower().strip('_')

class Services:
    def inject(self, services):
        self.services = {build_name(serv): serv for serv in services}



    def __getattr__(self, name):
        try:
            return self.services[name]
        except KeyError:
            raise AttributeError(name)
