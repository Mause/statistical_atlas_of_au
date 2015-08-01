

class Services:
    def services(self):
        try:
            return self._services
        except AttributeError:
            return self._load_services()

    def _load_services(self):
        self._services = []

    def __getattr__(self, name):
        try:
            return self.services[name]
        except KeyError:
            raise AttributeError
