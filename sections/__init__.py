SERVICES = [
    'aus_map.AusMap',
    'towns.TownsData'
]


class Singleton(type):
    def __call__(cls, *args, **kw):
        if hasattr(cls, '_instance'):
            return cls._instance

        cls._instance = cls.__new__(cls)
        cls._instance.__init__(*args, **kw)

        return cls._instance
