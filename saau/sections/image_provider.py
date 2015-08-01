import json
import inspect
from os.path import join, exists


def not_implemented():
    frame_info = inspect.currentframe().f_back
    msg = ''

    if 'self' in frame_info.f_locals:
        self = frame_info.f_locals['self']
        try:
            msg += self.__name__ + '#'  # for static/class methods
        except AttributeError:
            msg += self.__class__.__name__ + '.'

    msg += frame_info.f_code.co_name + '()'

    return NotImplementedError(msg)


class RequiresData:
    def __init__(self, data_dir, services):
        self.data_dir = data_dir
        self.services = services

    def has_required_data(self):
        raise not_implemented()

    def obtain_data(self):
        raise not_implemented()

    def data_dir_exists(self, name):
        return exists(self.data_dir_join(name))

    def data_dir_join(self, name):
        return join(self.data_dir, name)

    def save_json(self, name, data):
        with open(self.data_dir_join(name), 'w') as fh:
            json.dump(data, fh, indent=4)
        return True

    def load_json(self, name):
        with open(self.data_dir_join(name)) as fh:
            return json.load(fh)


class ImageProvider(RequiresData):
    def build_image(self, output_filename):
        raise not_implemented()
