from __future__ import annotations

import logging
import os
from pathlib import Path

import natsort
import unidecode


def create_thumb(file_path):
    """Create thumbnail from video file path using ffmpeg CLI

    Args:
        file_path (str): video file path

    Returns:
        str: created thumbnail file path
    """

    path_dir = os.path.split(file_path)[0]
    file_name = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name)[0]
    file_name_output = file_name_without_extension + ".jpg"
    file_path_output = os.path.join(path_dir, file_name_output)
    if os.path.exists(file_path_output):
        os.remove(file_path_output)
    # create thumb
    os.system(
        f'ffmpeg -v quiet -stats -y -i "{file_path}" -vframes 1 "{file_path_output}"'
    )
    return file_path_output


def create_txt(file_path, stringa):

    file = open(file_path, "w", encoding="utf8")
    file.write(stringa)
    file.close()


def get_txt_content(file_path):

    list_encode = ["utf-8", "ISO-8859-1"]  # utf8, ANSI
    for encode in list_encode:
        try:
            file = open(file_path, "r", encoding=encode)
            file_content = file.readlines()
            file_content = "".join(file_content)
            file.close()
            return file_content
        except:
            continue

    raise Exception("encode", f"Cannot open file: {file_path}")


def get_all_file_path(folder_path: Path, sort=True) -> dict[str, list[Path]]:
    """Returns List of all file paths inside a folder, recursively.
    Option to Sort naturally.

    Args:
    -----
        folder_path (Path): folder path
        sort (bool, optional): Return classified. Defaults to True.

    Returns:
    --------
        dict[str, list[Path]]: keys: ['content', 'errors']. values: list[Path]
    """

    def iter_folder(
        sub_folder,
        list_file_path: list[Path] = [],
        list_error: list[Path] = [],
    ) -> tuple[list[Path], list[Path]]:

        for x in sub_folder.iterdir():
            if not x.exists():
                logging.error("path_too_long: %s", x)
                list_error.append(x)
                continue
            if x.is_dir():
                iter_folder(x, list_file_path, list_error)
            else:
                list_file_path.append(x)
        return list_file_path, list_error

    if not folder_path.exists():
        logging.error("Folder not exists: %s", folder_path)
        raise FileNotFoundError(f"Folder not exists: {folder_path}")

    list_file_path, list_error = iter_folder(folder_path)

    if sort:
        list_file_path = natsort.natsorted(
            list_file_path, lambda x: unidecode.unidecode(str(x).lower())
        )
        list_error = natsort.natsorted(
            list_error, lambda x: unidecode.unidecode(str(x).lower())
        )

    return {"content": list_file_path, "errors": list_error}
