import logging

# import cartopy.crs as ccrs
# import matplotlib.pyplot as plt

from .data import LandcoverImageProvider, load_data
# from ..aus_map import get_map


class WheatImageProvider(LandcoverImageProvider):
    def build_image(self):
        # aus_map = get_map()

        logging.info('Loading data')
        df = load_data(self.data_dir)
        logging.info('Data loaded')

        from collections import defaultdict
        counts = defaultdict(lambda: 0)
        for thing in df:
            if thing:
                counts[thing['TERTIARY_V']] += 1

        with open('counts.txt', 'w') as fh:
            for name, count in sorted(counts.items(), key=lambda q: q[1]):
                fh.write('{} -> {}\n'.format(name, count))

        logging.info('Fin')

        # import IPython
        # IPython.embed()

        # aus_map.add_geometries(
        #     shpfile.geometries(),
        #     ccrs.PlateCarree(),
        #     # facecolor='LightGrey', edgecolor='black',
        #     facecolor='blue', edgecolor='red',
        #     zorder=0
        # )

        # plt.savefig(output_filename)
