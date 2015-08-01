SERVICES = [
    'aus_map.AusMap',
    'towns.TownsData'
]


def get_key(cls):
    return cls.__module__ + '.' + cls.__name__


def instance(cls):
    try:
        return Singleton.table[get_key(cls)]
    except KeyError:
        raise KeyError('Singleton uninitialized')


class Singleton(type):
    table = {}

    def __init__(cls, object_or_name, bases, attrs):
        cls.instance = classmethod(instance)

    def __call__(cls, *args, **kw):
        key = get_key(cls)

        try:
            return Singleton.table[key]
        except KeyError:
            pass

        Singleton.table[key] = cls.__new__(cls)
        Singleton.table[key].__init__(*args, **kw)

        return Singleton.table[key]
