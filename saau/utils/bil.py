import rasterio


def open_bil(base):
    with rasterio.drivers():
        bil = rasterio.open(base + '.bil')
        return bil.meta, bil.read()[0]
