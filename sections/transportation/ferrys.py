# from . import has_required_data_maker, obtain_data_maker

PATH = 'ferry_paths.json'


def has_required_data(data_dir):
    return False


# def obtain_data(data_dir):
#     with open(join(data_dir, PATH), 'w') as fh:
#         json.dump(get_paths(['Railways']).tolist(), fh)
