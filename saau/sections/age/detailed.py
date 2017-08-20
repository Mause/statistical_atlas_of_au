import random

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from ..image_provider import ImageProvider


STATES = np.array([
    ('Western Australia', 'WA'),
    ('South Australia', 'SA'),
    ('Tasmania', 'Tas'),
    ('New South Wales', 'NSW'),
    ('Queensland', 'Qld'),
    ('Northern Territory', 'NT'),
    ('Victoria', 'Vic')
])


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
sns.set_style("whitegrid")


def generate():
    for state in STATES[::, 1]:
        for age in RANGES[::, 1]:
            for gender in ['Males', 'Females']:
                yield {
                    'frequency': random.randint(10, 100),
                    'state': state,
                    'sex': gender
                }


class DetailedAgeImageProvider(ImageProvider):
    has_required_data = lambda _: True

    def build_image(self):
        fig, ax = plt.subplots(nrows=2, ncols=1)

        data = pd.DataFrame(list(generate()))

        state_rows = [
            ['WA', 'SA', 'Tas', 'NSW'],
            ['Qld', 'NT', 'Vic']
        ]

        for idx, subax in enumerate(ax):
            to_display = data[data.state.isin(state_rows[idx])]
            sns.violinplot(
                ax=subax,
                x="state",
                y="frequency",
                hue="sex",
                data=to_display,
                palette="Set2",
                split=True,
                scale="count"
            )
            subax.set_ylabel('')
            subax.set_xlabel('')
            subax.set_yticklabels(RANGES[::, 0][::-1])
            subax.set_yticks(list(map(int, RANGES[::, 1][::-1])))
            subax.legend_.remove()

            subax.set_ylim(0, 100)

        return fig
