SERVICES = [
    'aus_map.AusMap',
    'towns.TownsData'
]


class Singleton(type):
    table = {}

    def __call__(cls, *args, **kw):
        key = cls.__module__ + '.' + cls.__name__

        try:
            return Singleton.table[key]
        except KeyError:
            pass

        Singleton.table[key] = cls.__new__(cls)
        Singleton.table[key].__init__(*args, **kw)

        return Singleton.table[key]
