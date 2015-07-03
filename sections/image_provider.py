
class RequiresData:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def has_required_data(self):
        raise NotImplementedError

    def obtain_data(self):
        raise NotImplementedError


class ImageProvider(RequiresData):
    def build_image(self, output_filename):
        raise NotImplementedError
