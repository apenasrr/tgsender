from __future__ import annotations

import logging
import os
import sys
import time
from ctypes import util
from datetime import datetime
from pathlib import Path

from pyrogram import Client, types

from .. import utils
from ..mediainfo import ffprobe


def logging_config():
    log_file_name = "api_telegram"
    logfilename = "log-" + log_file_name + ".txt"
    logging.basicConfig(
        level=logging.warning,
        format=" %(asctime)s-%(levelname)s-%(message)s",
        handlers=[logging.FileHandler(logfilename, "w", "utf-8")],
    )
    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(logging.warning)
    # set a format which is simpler for console use
    formatter = logging.Formatter(" %(asctime)s-%(levelname)s-%(message)s")
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)


def ensure_connection():

    logging.warning("Ensuring connection...")
    if Path("user.session").exists():
        try:
            with Client(
                "user", workdir=Path("user.session").absolute().parent
            ) as app:
                message = app.send_message(
                    "me", text="telegram filesender-Connected..."
                )
                message.delete()
            return
        except:
            print("Delete Session file and try again.")
            return
    while True:
        try:
            api_id = int(input("Enter your api_id: "))
            api_hash = input("Enter your api_hash: ")

            with Client(
                "user",
                api_id,
                api_hash,
                workdir=Path("user.session").absolute().parent,
            ) as app:
                message = app.send_message(
                    "me", text="telegram filesender-Connected..."
                )
                message.delete()
            return
        except:
            print("\nError. Try again.\n")
            pass


# Keep track of the progress while uploading
def progress(current, total):

    stringa = f"{current * 100 / total:.1f}%"
    sys.stdout.write(stringa)
    sys.stdout.flush()
    sys.stdout.write("\b" * len(stringa))
    sys.stdout.flush()


def get_video_metadata(file_path):

    try:
        metadata = ffprobe(file_path).get_output_as_dict()
        metadata_streams = metadata["streams"]
        video_metadata = metadata_streams[0]
    except:
        # case of error, show all file metadata
        print(file_path)
        print(ffprobe(file_path).get_output_as_dict())
        metadata = ffprobe(file_path).get_output_as_dict()
        metadata_streams = metadata["streams"]
        video_metadata = metadata_streams[0]
    try:
        width = video_metadata["width"]
    except:
        video_metadata = metadata_streams[1]
    try:
        width = video_metadata["width"]
        height = video_metadata["height"]
        duration = int(float(metadata["format"]["duration"]))
        return {"width": width, "height": height, "duration": duration}
    except Exception as e:
        logging.error(f"File Error: {file_path}.\napi_telegram.py line 63")
        raise ValueError(e)


def send_sticker(chat_id, sticker):

    logging.warning("Sending sticker...")
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_sticker(chat_id, sticker)
        return return_


def send_video(chat_id, file_path, caption, log_file_path=None):

    logging.warning("Sending video...")
    video_metadata = get_video_metadata(file_path)
    thumb = utils.create_thumb(file_path)
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_video(
            chat_id,
            file_path,
            caption=caption,
            progress=progress,
            supports_streaming=True,
            width=video_metadata["width"],
            height=video_metadata["height"],
            duration=video_metadata["duration"],
            thumb=thumb,
        )
        os.remove(thumb)

    if log_file_path:
        utils.log_send_return(str(return_), file_path, Path(log_file_path))


def send_audio(chat_id, file_path, caption, log_file_path=None):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        logging.warning("Sending audio...")
        return_ = app.send_audio(
            chat_id, file_path, caption=caption, progress=progress
        )
    if log_file_path:
        utils.log_send_return(str(return_), file_path, log_file_path)


def send_document(chat_id, file_path, caption, log_file_path=None):

    logging.warning("Sending document...")
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_document(
            chat_id, file_path, caption=caption, progress=progress
        )

    if log_file_path:
        utils.log_send_return(str(return_), file_path, Path(log_file_path))


def send_photo(chat_id, file_path, caption, log_file_path=None):

    logging.warning("Sending photo...")
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_photo(
            chat_id, file_path, caption=caption, progress=progress
        )
    if log_file_path:
        utils.log_send_return(str(return_), file_path, log_file_path)


def send_message(chat_id, text):

    logging.warning("Sending message...")
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_message(
            chat_id, text=text, disable_web_page_preview=True
        )
    return return_


def pin_chat_message(chat_id, message_id):

    logging.warning("Pinning message...")
    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.pin_chat_message(
            chat_id, message_id=message_id, both_sides=True
        )
    return return_


def get_messages(chat_id, message_ids):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.get_messages(chat_id, message_ids)
    return return_


def get_history(chat_id):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.get_history(chat_id)
    return return_


def get_list_media_doc(list_dict_sent_doc):
    """
    Generates a list of "inputmediadocument"
     from a list of 'return of sent files'.
    Used to forward files in album format with 'send_media_group' method

    Args:
        list_dict_sent_doc (list):
            List of returns from many files sent by the send_document method

    Returns:
        list: list of InputMediaDocument pyrogram type,
               necessary to send_media_group method
    """

    list_media_doc = []
    for dict_sent_doc in list_dict_sent_doc:
        file_id = dict_sent_doc["file_id"]
        caption = dict_sent_doc["caption"]
        media = types.InputMediaDocument(media=file_id, caption=caption)

        list_media_doc.append(media)
    return list_media_doc


def send_media_group(chat_id, list_media):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.send_media_group(chat_id, media=list_media)
    return return_


def delete_messages(chat_id, list_message_id):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.delete_messages(
            chat_id=chat_id, message_ids=list_message_id
        )
    return return_


def send_file(dict_file_data, chat_id, time_limit=20, log_file_path=None):

    file_path = dict_file_data.get("file_output")
    if file_path is None:
        file_path = dict_file_data.get("file_path")
    description = dict_file_data["description"]
    file_extension = Path(file_path).suffix.lower()
    if file_extension == ".mp4":
        type_file = "video"
    elif file_extension in [".mp3", ".aac"]:
        type_file = "audio"
    elif file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
        type_file = "photo"
    else:
        type_file = "document"

    dict_params = {
        "chat_id": chat_id,
        "file_path": file_path,
        "caption": description,
        "log_file_path": str(log_file_path),
    }
    sec_time_out = time_limit * 60
    if type_file == "video":
        utils.time_out(sec_time_out, send_video, dict_params, restart=True)
    elif type_file == "audio":
        utils.time_out(sec_time_out, send_audio, dict_params, restart=True)
    elif type_file == "photo":
        utils.time_out(sec_time_out, send_photo, dict_params, restart=True)
    elif type_file == "document":
        utils.time_out(sec_time_out, send_document, dict_params, restart=True)


def send_files(
    list_dict: list[dict],
    chat_id: int,
    time_limit: int = 20,
    folder_path_project: Path = None,
):
    """Sends a series of files to the same chat_id

    Args:
        list_dict (list[dict]):
            list of dict. dict with keys:
                file_path: Absolute file_path
                description: file description
                file_output: Absolute file_path for log
        chat_id (int):
            chat id to send
        time_limit (int):
            time limit for upload before rebooting automatically
        folder_path_project (Path):
            Folder where Logs folder will be created
    """

    list_log_file_path = []
    len_list_dict = len(list_dict)

    for index, d in enumerate(list_dict):
        order = index + 1
        file_path = d.get("file_path")
        file_output = d.get("file_output")
        if not file_output:
            file_output = Path(d["file_path"]).name
        else:
            file_output = file_output.name
        if folder_path_project:
            log_file_path = utils.get_log_file_path(
                Path(folder_path_project), Path(file_path), index
            )
        if not Path(file_path).exists():
            logging.error(f"file not exist. {file_output}")
            continue

        logging.warning(f"{order}/{len_list_dict} Uploading: {file_output}")

        file_extension = Path(file_path).suffix
        description = d["description"]

        if file_extension == ".mp4":
            type_file = "video"
        elif file_extension == ".mp3":
            type_file = "audio"
        elif file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
            type_file = "photo"
        else:
            type_file = "document"

        dict_params = {
            "chat_id": chat_id,
            "file_path": file_path,
            "caption": description,
            "log_file_path": log_file_path,
        }
        sec_time_out = time_limit * 60
        while True:
            try:
                if type_file == "video":
                    utils.time_out(
                        sec_time_out, send_video, dict_params, restart=True
                    )
                elif type_file == "audio":
                    utils.time_out(
                        sec_time_out, send_audio, dict_params, restart=True
                    )
                elif type_file == "photo":
                    utils.time_out(
                        sec_time_out, send_photo, dict_params, restart=True
                    )
                elif type_file == "document":
                    utils.time_out(
                        sec_time_out, send_document, dict_params, restart=True
                    )
                break
            except Exception as e:
                print(e)
                print("\nError. Trying again...")
                time.sleep(30)
                continue
        list_log_file_path.append(log_file_path)
    return list_log_file_path


def create_channel(title, description):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_chat = app.create_channel(title=title, description=description)
    chat_id = return_chat.id
    return chat_id


def add_chat_members(chat_id, user_ids):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        app.add_chat_members(chat_id=chat_id, user_ids=user_ids)


def promote_chat_members(chat_id, user_ids):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:

        privileges_config = types.ChatPrivileges(
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_promote_members=True,
        )

        for user_id in user_ids:
            app.promote_chat_member(
                chat_id=chat_id, user_id=user_id, privileges=privileges_config
            )


def set_chat_description(chat_id, description):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        app.set_chat_description(chat_id=chat_id, description=description)


def export_chat_invite_link(chat_id):

    with Client("user", workdir=Path("user.session").absolute().parent) as app:
        return_ = app.export_chat_invite_link(chat_id=chat_id)

    return return_


def get_template(folder_path_descriptions, file_name):

    template_path = Path(folder_path_descriptions) / file_name
    if not template_path.exists():
        template_path = (
            Path(__file__).absolute().parent.parent / "template" / file_name
        )
    if not template_path.exists():
        raise FileNotFoundError(f"{template_path=}")
    return template_path


def get_channel_title(folder_path_descriptions):

    header_project_name = "header_project.txt"
    header_project_path = get_template(
        folder_path_descriptions, header_project_name
    )

    channel_info_stringa = utils.get_txt_content(header_project_path)
    list_channel_info = channel_info_stringa.split("\n")

    title = list_channel_info[0]
    return title


def get_channel_description(chat_invite_link, folder_path_descriptions):

    header_template_name = "header_project.txt"
    header_template_path = get_template(
        folder_path_descriptions, header_template_name
    )

    channel_info_stringa = utils.get_txt_content(header_template_path)
    list_channel_info = channel_info_stringa.split("\n")

    description = "\n".join(list_channel_info[1:])
    description = description.replace("{chat_invite_link}", chat_invite_link)
    return description


def get_list_adms(channel_adms: str):

    if not channel_adms:
        return []
    channel_adms_stringa_list = channel_adms.split(",")
    list_adms = []
    for line in channel_adms_stringa_list:
        list_adms.append(line.strip())
    return list_adms
