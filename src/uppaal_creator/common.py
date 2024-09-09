import os
from typing import Union


NodeType = Union[int, str]


class FileManager:
    def __init__(self, base_dir: str, auto_create_folder=True) -> None:
        self.dir = os.path.abspath(base_dir)
        self.auto_create_folder = auto_create_folder
        if self.auto_create_folder:
            self.ensure_folder_exist(self.dir)
        assert os.path.exists(self.dir)

    def get_abspath(self, file_relpath: str) -> str:
        return os.path.abspath(os.path.join(self.dir, file_relpath))

    def ensure_folder_exist(self, folder_path: str):
        folder_path = self.get_abspath(folder_path)
        if self.auto_create_folder:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
