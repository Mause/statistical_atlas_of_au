from os.path import join, exists

from matplotlib import font_manager

from ...sections.image_provider import RequiresData
from ...utils.download import get_binary
from ...utils import unzip


SERVICES = ['__init__.FontProvider']


class FontProvider(RequiresData):
    service_name = 'fonts'

    FILENAME = 'Fontscafe_HandShopTypography-C30_demo'

    def path(self):
        return self.data_dir_join(
            join(
                self.FILENAME,
                self.FILENAME + ".ttf"
            )
        )

    def has_required_data(self):
        return exists(self.path())

    def obtain_data(self):
        filename = self.data_dir_join(self.FILENAME + ".zip")
        res = get_binary(
            'http://dl.dafont.com/dl/?f=hand_shop_typography_c30',
            filename
        )
        if not res:
            return res

        unzip(filename)

        return self.has_required_data()

    def get_font(self):
        return font_manager.FontProperties(fname=self.path())
