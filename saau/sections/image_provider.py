import inspect
import json
from os.path import exists, join
from pathlib import Path
from typing import Any, Union
from abc import ABC, abstractmethod

from ..services import Services

PathOrStr = Union[str, Path]


def not_implemented():
    frame = inspect.currentframe()
    assert frame
    frame_info = frame.f_back
    assert frame_info
    msg = ''

    if 'self' in frame_info.f_locals:
        self = frame_info.f_locals['self']
        try:
            msg += self.__name__ + '#'  # for static/class methods
        except AttributeError:
            msg += self.__class__.__name__ + '.'

    msg += frame_info.f_code.co_name + '()'

    return NotImplementedError(msg)


class RequiresData(ABC):
    def __init__(self, data_dir: Path, services: Services) -> None:
        self.data_dir = data_dir
        self.services = services

    @abstractmethod
    def has_required_data(self) -> bool:
        raise not_implemented()

    def obtain_data(self) -> bool:
        raise not_implemented()

    def data_dir_exists(self, name: PathOrStr) -> bool:
        return exists(self.data_dir_join(name))

    def data_dir_join(self, name: PathOrStr) -> str:
        return join(self.data_dir, name)

    def save_json(self, name: PathOrStr, data: Any) -> bool:
        import pandas as pd

        if isinstance(data, (pd.DataFrame, pd.Series)):
            data.to_json(self.data_dir_join(name))
        else:
            with open(self.data_dir_join(name), 'w') as fh:
                json.dump(data, fh, indent=4)
        return True

    def load_json(self, name: PathOrStr) -> Any:
        with open(self.data_dir_join(name)) as fh:
            return json.load(fh)


class ImageProvider(RequiresData):
    @abstractmethod
    def build_image(self) -> str:
        raise not_implemented()
