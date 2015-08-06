from shapely.geometry import Polygon


def boundary_to_polygon(boundary, swap=False):
    pairs = boundary.split('; ')
    pairs = [pair.split(', ') for pair in pairs]
    return raw_boundary_to_polygon(
        [tuple(map(float, pair)) for pair in pairs],
        swap
    )


def raw_boundary_to_polygon(boundary, swap=False):
    # Lat = Y Long = X

    top_left, bottom_right = boundary

    bottom_left = (bottom_right[0], top_left[1])
    top_right = (top_left[0], bottom_right[1])

    points = [
        top_left,
        top_right,
        bottom_right,
        bottom_left,
        top_left
    ]

    if swap:
        points = [point[::-1] for point in points]

    return Polygon(points)
