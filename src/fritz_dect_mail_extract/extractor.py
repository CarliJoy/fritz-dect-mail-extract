import getpass
import logging
import os
import re
from dataclasses import dataclass, fields
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

import imap_tools
import pandas as pd
from imap_tools import ImapToolsError

from .constants import ENV_NAMES
from .exceptions import ExtractionError, MultipleAttachments

_logger = logging.getLogger(__name__)

FileName = str
FileData = Tuple[FileName, bytes]

date_regex = re.compile(r"\d\d[.]\d\d[.]\d\d\d\d")


@dataclass
class ServerData:
    server: str
    username: str
    password: str


@dataclass
class MailRawData:
    subject: str
    date: datetime
    html: str
    temperature_png: FileData
    energy_png: FileData
    data_csv: FileData

    @property
    def file_fields(self) -> List[str]:
        return [
            field.name
            for field in fields(self)
            if field.name not in ["date", "subject"]
        ]

    @property
    def subject_date_string(self) -> str:
        return date_regex.findall(self.subject)[0]

    @property
    def dataframe(self) -> pd.DataFrame:
        def my_date_parse(in_str) -> datetime:
            if len(in_str) == 5:
                # Only time given so add date
                in_str = f"{self.subject_date_string} {in_str}"
            date = datetime.strptime(in_str, "%d.%m.%Y %H:%M")
            return date

        s = str(self.data_csv[1], "UTF-8")

        df = pd.read_csv(
            StringIO(s), skiprows=1, sep=";", decimal=",", usecols=[0, 1, 2]
        )
        df["Datum/Uhrzeit"] = df["Datum/Uhrzeit"].apply(my_date_parse)
        df.set_index("Datum/Uhrzeit", inplace=True)
        return df


def get_user_value(
    var_name: str,
    inputs: Dict[str, Optional[str]],
    *,
    interactive: bool,
    secure: bool = False,
) -> str:
    """
    Try to extract the user input for the given var_name by checking values in the
    following order
      * Command Line Input
      * Environmental Variable
      * Ask for user input if interactive mode
    """
    if inputs[var_name]:
        return inputs[var_name]
    if env_value := os.environ.get(ENV_NAMES[var_name.upper()]):
        return env_value
    if interactive:
        ask_string = f"{var_name.capitalize()}: "
        if secure:
            try:
                import keyring
            except ImportError:
                pass
            else:
                # Try to extract password from secret service
                _logger.info(
                    f"Getting secret for server: '{inputs['server']}', "
                    f"user: '{inputs['username']}'"
                )
                password = ""  # nosec
                try:
                    password = keyring.get_password(
                        inputs["server"], inputs["username"]
                    )
                except Exception as e:
                    _logger.exception("Failed to get password with keyring", exc_info=e)
                if not password:
                    password = getpass.getpass(ask_string)

                try:
                    # set password to secret server
                    keyring.set_password(inputs["server"], inputs["username"], password)
                except Exception as e:
                    _logger.exception("Failed save password in keyring", exc_info=e)
                return password
        else:
            return input(ask_string)
    raise ValueError(f"Value for '{var_name}' was not given!")


def get_server_data(
    server: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    interactive: bool = True,
) -> ServerData:
    server = get_user_value("server", locals(), interactive=interactive)
    username = get_user_value("username", locals(), interactive=interactive)
    password = get_user_value(
        "password", locals(), interactive=interactive, secure=True
    )
    return ServerData(
        server=server,
        username=username,
        password=password,
    )


def find_and_extract_mails(
    server_data: ServerData,
) -> Generator[MailRawData, None, None]:
    def set_if_not_given(
        dictionary: Dict[str, Union[None, str, FileData]],
        key: str,
        attachment: imap_tools.MailAttachment,
    ):
        if dictionary.get(key) is not None:
            raise MultipleAttachments(
                f"There was already an attachment '{key}' given for the current "
                "mail. attachment given were: \n"
                f" * {dictionary.get(key)[0]} \n"
                f" * {attachment.filename} \n"
            )
        dictionary[key] = (attachment.filename, attachment.payload)

    try:
        with imap_tools.MailBox(server_data.server).login(
            server_data.username, server_data.password
        ) as mailbox:
            for msg in mailbox.fetch(imap_tools.AND(subject="FRITZ!DECT")):
                raw_data = {
                    "html": msg.html,
                    "date": msg.date,
                    "subject": msg.subject,
                    "data_csv": None,
                    "temperature_png": None,
                    "energy_png": None,
                }
                for attachment in msg.attachments:
                    if attachment.filename.endswith(".csv"):
                        set_if_not_given(raw_data, "data_csv", attachment)
                    if attachment.filename.endswith(".png"):
                        if attachment.filename.startswith("ha_temp"):
                            set_if_not_given(raw_data, "temperature_png", attachment)
                        if attachment.filename.startswith("ha_stat"):
                            set_if_not_given(raw_data, "energy_png", attachment)
                empty = [key for key, val in raw_data.items() if val is None]
                if empty:
                    _logger.warning(
                        f"Ignoring {msg.subject} from {msg.date} as the following "
                        f"attachment(s) {','.join(empty)} were missing."
                    )
                else:
                    yield MailRawData(**raw_data)
    except ImapToolsError as e:
        raise ExtractionError(e)


def get_filename_prefix(mail: MailRawData) -> str:
    return f"{mail.date:%Y-%m-%d_%H-%M-%S}_FritzDect_"


def save_file(target_folder: Path, key: str, mail: MailRawData) -> str:
    filename = get_filename_prefix(mail)
    if key == "html":
        filename += "mail.html"
        data = mail.html.encode("UTF-8")
    else:
        filename += key.replace("_", ".")
        data = getattr(mail, key)[1]
    file_path = target_folder / filename
    with file_path.open(mode="wb") as f:
        f.write(data)
    return str(file_path.absolute())


def save_to_folder(mail: MailRawData, target_folder: Path) -> None:
    for field in mail.file_fields:
        file = save_file(target_folder, field, mail)
        _logger.debug(f"Saved '{file}'")


def do_extract(server_data: ServerData, target_folder: Path) -> None:
    df: Optional[pd.DataFrame] = None
    for mail in find_and_extract_mails(server_data):
        if df is None:
            df = mail.dataframe
        else:
            df = df.append(mail.dataframe)
        save_to_folder(mail, target_folder)
        _logger.info(f"Extracted '{mail.subject}'")
    combined_path = target_folder / "combined.csv"
    df.to_csv(combined_path)
    _logger.info(f"Wrote '{combined_path}'")
