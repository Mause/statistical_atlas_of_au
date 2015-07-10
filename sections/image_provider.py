import inspect


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
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def has_required_data(self):
        raise not_implemented()

    def obtain_data(self):
        raise not_implemented()


class ImageProvider(RequiresData):
    def build_image(self, output_filename):
        raise not_implemented()
