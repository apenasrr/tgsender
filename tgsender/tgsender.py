import logging
import os
import sys
import time
from configparser import ConfigParser
from pathlib import Path

import pandas as pd
import pyautogui as pag
import pyperclip

from . import utils
from .api import (
    add_chat_members,
    create_channel,
    ensure_connection,
    export_chat_invite_link,
    get_channel_description,
    get_channel_title,
    get_list_adms,
    promote_chat_members,
    send_file,
    set_chat_description,
)


def get_config_data(path_file_config):
    """get default configuration data from file config.ini

    Returns:
        dict: config data
    """

    config_file = ConfigParser()
    config_file.read(path_file_config)
    default_config = dict(config_file["default"])
    return default_config


def gen_data_frame(list_file_path: list[Path]):

    list_dict = [
        {"description": file_path.name, "file_output": file_path}
        for file_path in list_file_path
    ]
    df = pd.DataFrame(list_dict)
    list_columns = ["file_output", "description"]
    df = df.reindex(list_columns, axis=1)
    return df


def create_report_descriptions(upload_plan_path):

    str_msg_paste_folder = "Paste the path folder with your files"
    str_msg_paste_here = "Paste here: "
    print(str_msg_paste_folder)
    while True:
        path_folder = input(str_msg_paste_here)
        if Path(path_folder).exists():
            all_file_path = utils.get_all_file_path(Path(path_folder))
            break
        else:
            logging.error("Folder not exist. Try again.")

    list_file_path = all_file_path["content"]
    df = gen_data_frame(list_file_path)
    df.to_csv(upload_plan_path, index=False)


def pag_hotkey(key_1, key_2):

    pag.keyDown(key_1)
    pag.keyDown(key_2)
    pag.keyUp(key_1)
    pag.keyUp(key_2)


def set_win_positions():
    """
    Keep the 'windows explorer' windows in front
    and telegram windows in back
    """

    pag_hotkey("alt", "tab")
    time.sleep(1)
    pag.keyDown("alt")
    pag.press("tab")
    time.sleep(0.5)
    pag.press("tab")
    pag.keyUp("alt")
    time.sleep(0.5)


def change_between_telegram_winexplorer():

    pag_hotkey("alt", "tab")
    time.sleep(2)


def get_next_video_to_send(path_file_description: Path):

    try:
        df = pd.read_csv(path_file_description)
    except Exception as e:
        print(f"Can't open file: {path_file_description}")
        print(e)

    mask_df_to_send = df["sent"].isin([0])
    df_to_send = df.loc[mask_df_to_send, :]
    count_files_to_send = df_to_send.shape[0]
    if count_files_to_send == 0:
        return 0, False
    else:
        file_index = df_to_send.index[0]
        df_to_send = df_to_send.reset_index(drop=True)
        dict_first_line = df_to_send.loc[0, :]
        return file_index, dict_first_line


def update_description_file_sent(path_file_description, dict_file_data):

    try:
        df = pd.read_csv(path_file_description)
    except Exception as e:
        print(f"Can't open file: {path_file_description}")
        print(e)

    file_path = dict_file_data["file_output"]
    mask_file_path = df["file_output"].isin([file_path])
    df_filter = df.loc[mask_file_path, :]
    len_df_filter = len(df_filter)
    if len_df_filter != 1:
        print(f"Find {len_df_filter} line for file: {file_path}")
        sys.exit()
    index_video = df_filter.index
    # update df
    df.loc[index_video, "sent"] = 1
    df.to_csv(path_file_description, index=False)


def ensure_existence_sent_column(df_list, file_path_descriptions):

    description_columns = df_list.columns
    if "sent" not in description_columns:
        df_list["sent"] = 0
        df_list.to_csv(file_path_descriptions, index=False)


def get_data_upload_plan(upload_plan_path_folder: Path) -> list[dict]:

    file_path_upload_plan = upload_plan_path_folder / "upload_plan.csv"
    df_upload_plan = pd.read_csv(file_path_upload_plan)
    data_upload_plan = df_upload_plan.to_dict("records")
    return data_upload_plan


def paste_on_telegram_app(desc):

    time.sleep(2)
    pag_hotkey("ctrl", "v")
    pyperclip.copy(desc)
    time.sleep(3)
    pag_hotkey("ctrl", "v")
    time.sleep(1)
    pag.press("enter")
    time.sleep(1)


def ask_send_app_or_api():

    str_msg_1 = "How do you intend to send the files?"
    str_msg_2 = "1-By telegram desktop app"
    str_msg_3 = "2-By telegram api (default)\n"
    str_msg_answer = "Type the number: "

    print("\n".join([str_msg_1, str_msg_2, str_msg_3]))

    answer = input(str_msg_answer)

    if answer == "":
        return 2

    return int(answer)


def send_via_telegram_app(data_upload_plan):

    set_win_positions()
    qt_files = len(data_upload_plan)
    print(f"Send {qt_files} files")
    time.sleep(0.5)

    for d in data_upload_plan:
        desc = d["description"]
        # copy file
        pag_hotkey("ctrl", "c")

        # change to telegram
        change_between_telegram_winexplorer()

        # paste on telegram app
        paste_on_telegram_app(desc)

        # change back to windows explorer and select next file
        change_between_telegram_winexplorer()
        pag.press("down")
        time.sleep(0.5)


def process_create_channel(folder_path_descriptions):

    # TODO: The channel title must be the name of the original project folder
    title = get_channel_title(folder_path_descriptions)
    description = "channel description"

    chat_id = create_channel(title=title, description=description)
    return chat_id


def config_channel(
    chat_id, chat_invite_link, list_adms, folder_path_descriptions
):

    description = get_channel_description(
        chat_invite_link, folder_path_descriptions
    )
    set_chat_description(chat_id=chat_id, description=description)

    if len(list_adms) != 0:
        add_chat_members(chat_id=chat_id, user_ids=list_adms)
        promote_chat_members(chat_id=chat_id, user_ids=list_adms)


def send_via_telegram_api(folder_path_upload_plan: Path, dict_config: dict):

    file_path_descriptions = folder_path_upload_plan / "upload_plan.csv"
    df_list = pd.read_csv(file_path_descriptions)

    ensure_existence_sent_column(df_list, file_path_descriptions)

    ensure_connection()

    chat_id = process_to_send_telegram(folder_path_upload_plan, dict_config)
    time_limit = int(dict_config["time_limit"])

    # Connection test to avoid infinite loop of asynchronous attempts
    # to send files without pause to fill connection pool

    files_count = df_list.shape[0]
    while True:
        index, dict_file_data = get_next_video_to_send(file_path_descriptions)
        # mark file as sent
        if dict_file_data is False:
            break
        else:
            file_path = dict_file_data["file_output"]
            print(f"{index+1}/{files_count} Uploading: {file_path}")

            send_file(dict_file_data, chat_id, time_limit)

            update_description_file_sent(
                file_path_descriptions, dict_file_data
            )


def test_chat_id(dict_config):

    if "chat_id" in dict_config.keys():
        chat_id = dict_config["chat_id"]
        is_int = isinstance(chat_id, int)
        if is_int:
            if chat_id < 0:
                return True
        print("config['chat_id'] must be negative integer")
        return False
    else:
        print("config['chat_id'] key 'chat_id' not found in config file")
        return False


def save_metadata_file(chat_id, chat_invite_link, file_path_metadata):

    dict_metadata = {"chat_id": chat_id, "chat_invite_link": chat_invite_link}
    utils.create_txt(file_path_metadata, str(dict_metadata))


def process_to_send_telegram(folder_path_descriptions, dict_config):
    """
    Creates a new properly configured channel
    or use the existing chat_id in the configuration file

    Args:
        folder_path_descriptions (str):
            folder path where the upload_plan.csv file is located
        dict_config (dict):
            configuration data.
            template: {chat_id:negative int, create_new_channel:boolean}

    Returns:
        int: chat_id. negative integer
    """

    # check if there is necessary to continue upload
    file_path_metadata = os.path.realpath(
        os.path.join(folder_path_descriptions, "channel_metadata")
    )
    continue_upload = False
    if os.path.exists(file_path_metadata):
        dict_metadata = eval(utils.get_txt_content(file_path_metadata))
        continue_upload = True

    # get chat_id
    # Create new channel-Default True
    if dict_config["create_new_channel"] == 0 or continue_upload:
        channel_new = False
    else:
        channel_new = True

    if channel_new:
        # create new channel
        chat_id = process_create_channel(folder_path_descriptions)
        chat_invite_link = export_chat_invite_link(chat_id=chat_id)
        save_metadata_file(chat_id, chat_invite_link, file_path_metadata)

        # config new channel
        list_adms = get_list_adms(dict_config["channel_adms"])
        config_channel(
            chat_id, chat_invite_link, list_adms, folder_path_descriptions
        )
    else:
        # use existent channel
        if continue_upload:
            dict_data = dict_metadata
        else:
            dict_data = dict_config

        chat_id_is_valid = test_chat_id(dict_data)
        if chat_id_is_valid:
            chat_id = dict_data["chat_id"]

    return chat_id


def ask_create_or_use(upload_plan_path):

    str_msg_create_or_use_1 = "About the upload_plan.csv report"
    str_msg_create_or_use_2 = "1-Use existing (default)"
    str_msg_create_or_use_3 = "2-Create a new one\n"
    str_msg_answer = "Type the number: "

    print(str_msg_create_or_use_1)
    print(str_msg_create_or_use_2)
    print(str_msg_create_or_use_3)

    create_or_use_answer = input(str_msg_answer)
    if create_or_use_answer == "2":
        create_report_descriptions(upload_plan_path)
        input("Report Created. Press a key to continue.")
    else:
        pass


def main():
    """
    An easy and automatic way to post a series of files to the telegram desktop
    app, along with personalized descriptions.

    How to use: https://github.com/apenasrr/Telegram_filesender/blob/master/README.md

    Args:
        upload_plan_path (str):
        dict_config (dict): {create_new_channel_flag: int, chat_id: int}
    """

    path_config_file = Path(__file__).absolute().parent / "config.ini"
    dict_config = get_config_data(path_config_file)

    upload_plan_path = Path("upload_plan.csv").absolute()
    ask_create_or_use(upload_plan_path)

    upload_plan_path_folder = upload_plan_path.parent
    data_upload_plan = get_data_upload_plan(upload_plan_path_folder)
    send_mode = ask_send_app_or_api()

    if send_mode == 1:
        send_via_telegram_app(data_upload_plan)
    elif send_mode == 2:
        send_via_telegram_api(upload_plan_path_folder, dict_config)


if __name__ == "__main__":

    main()
