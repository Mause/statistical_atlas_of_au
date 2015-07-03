import json
from os.path import expanduser

import pandas
import numpy as np
import matplotlib.pyplot as plt

from ..aus_map import get_map

filename = (
    'ABS_ANNUAL_ERP_LGA2014_Data_e7f16b2f-edf9-4da4-9cbc-4d2e06154315.csv'
)


def get_data():
    df = pandas.read_csv(filename)

    dat = df[df.Time == 2014]
    return dat[dat['Region Type'] == 'Local Government Areas (2014)']


def get_towns():
    with open(expanduser('~/Dropbox/fuelwatch/data/towns.json')) as fh:
        towns = json.load(fh)

    return {
        name.split(',')[0].strip(): loc
        for name, loc in towns.items()
    }


clean_region = lambda region: ' '.join(region.split()[:-1])


def is_locatable(towns):
    return lambda row: clean_region(row.Region) in towns


def main():
    print('loading towns')
    towns = get_towns()
    print('loading data')
    dat = get_data()

    print('finding towns')
    locatable = dat[dat.apply(is_locatable(towns), 1)]

    print('annotating towns')
    populations = locatable.apply(
        lambda thing: (
            (thing.Value,) +
            tuple(towns[clean_region(thing.Region)])
        ),
        1
    )

    populations = np.array(populations)
    populations = np.array(list(map(np.array, populations)))

    heat = populations[::, 0]
    x = populations[::, 1]
    y = populations[::, 2]

    print('building map')

    colors = np.zeros((len(x), len(y)))
    for sx, sy, sc in zip(range(len(x)), range(len(y)), heat):
        colors[sx][sy] = sc

    get_map()  # bah, globals
    # print('mapping towns')

    # import cartopy.crs as ccrs
    # rotated_pole = ccrs.RotatedPole(pole_longitude=177.5, pole_latitude=37.5)

    # plt.pcolor(x, y, colors, cmap='hot_r', transform=rotated_pole)

    print('showing \'em')
    plt.savefig('town_populations.png')

if __name__ == '__main__':
    main()
