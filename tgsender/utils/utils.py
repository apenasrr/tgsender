from __future__ import annotations

import json
import logging
import os
from hashlib import md5
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


def get_log_file_path(
    folder_path_project: Path, file_path_origin: Path, index: int
) -> Path:
    """get path of log file to be sent
    Change origin file name to avoid duplicate name in the log folder
     Change based on the path of the folder of the origin file

    Args:
        folder_path_project (Path): path of project folder,
            where will be created the log_sent folder
        file_path_origin (Path): path of file
        index (int): file index in a row

    Returns:
        Path: path of log file
    """

    folder_path_log_sent = folder_path_project / "log_sent"
    if not folder_path_log_sent.exists():
        folder_path_log_sent.mkdir()

    hash_sufix = md5(
        str(file_path_origin.parent).encode(encoding="utf-8")
    ).hexdigest()[:5]
    extension = file_path_origin.suffix.replace(".", "")
    log_file_name = (
        str(index)
        + "-"
        + file_path_origin.stem
        + "_"
        + extension
        + "_"
        + hash_sufix
        + ".json"
    )
    log_file_path = folder_path_log_sent / log_file_name
    return log_file_path


def log_send_return(
    return_message: str, file_path: Path, log_file_path: Path
) -> bool:
    """Save json file of pyrogram message return from send_file method
    with additional key 'file_origin', that is the path of file that was sent

    Args:
        return_message (str): pyrogram message return
        file_path (Path): path of file that was sent
        log_file_path (Path): json file of sent log
    Return:
        bool: True If log_file was successfully saved
    """

    dict_return = json.loads(return_message)
    dict_return["file_origin"] = str(file_path)
    json.dump(
        dict_return, open(log_file_path, "w", encoding="utf-8"), indent=2
    )
    return log_file_path.exists()


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
