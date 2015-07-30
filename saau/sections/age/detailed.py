import random

import numpy as np
import matplotlib.pyplot as plt

from ..image_provider import ImageProvider


STATES = [
    ('Western Australia', 'WA'),
    ('South Australia', 'SA'),
    ('Tasmania', 'Tas'),
    ('New South Wales', 'NSW'),
    ('Queensland', 'Qlds'),
    ('Northern Territory', 'NT'),
    ('Victoria', 'Vic')
]


RANGES = np.array([
    ('85 and older', 85),
    ('70', 70),
    ('60', 60),
    ('50', 50),
    ('40', 40),
    ('30', 30),
    ('20', 20),
    ('10', 10),
    ('Under 5', 5)
])

random.seed(200)


class DetailedAgeImageProvider(ImageProvider):
    has_required_data = lambda _: True

    def build_image(self, q):
        fig, ax = plt.subplots(
            nrows=2,
            ncols=4
        )

        for idx, (state, abbr) in enumerate(STATES):
            for gender in ['Males', 'Females']:
                sax = ax.flat[idx]

                width = np.arange(len(RANGES))
                if gender == 'Males':
                    width = -width

                sax.set_xticks([])
                sax.barh(
                    [
                        random.randint(10, 100)
                        for _ in range(len(RANGES))
                    ],
                    width=width,
                )

        for row in ax:
            row[0].set_yticks(list(range(0, 100, 10)))
            row[0].set_yticklabels(RANGES[::, 0], fontsize=8)

            for thing in row[1:]:
                thing.set_yticks([])
                thing.set_yticklabels([])

        for thing in ax[1][[-1, -2]]:
            fig.delaxes(thing)

        # for thing in ax[1][:-2]:
        #     import IPython
        #     IPython.embed()

        fig.tight_layout()
        plt.grid()

        return fig
