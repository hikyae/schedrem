import json
import logging
import sys
from pathlib import Path

import psutil
from pydantic import ValidationError
from yaml import YAMLError

from .config import ActionConfig
from .manager import SchedremManager
from .util import (
    Messenger,
    error_message,
    get_args,
    get_config_file,
    set_logger,
    take_action,
)


def action_mode(action) -> None:
    try:
        action = ActionConfig(**json.loads(action))
        status = take_action(action)
    except ValidationError as e:
        m = Messenger()
        m.warning(error_message(e.errors()))
        status = 1
    except Exception as e:
        msg = f"{e.__class__.__name__}, {e}"
        m = Messenger()
        m.warning(msg)
        status = 1
    sys.exit(status)


def manager_mode(config) -> None:
    if config:
        yaml_path = Path(config).resolve()
    else:
        try:
            yaml_path = get_config_file()
        except Exception as e:
            msg = f"{e.__class__.__name__}, {e}\nProgram exits."
            m = Messenger()
            m.error(msg)
            sys.exit(msg)

    logging.debug("config path: %s\n", yaml_path)

    if (
        len(
            [
                proc
                for proc in psutil.process_iter(["name", "cmdline"])
                if proc.info["name"] in ("schedrem", "schedrem.exe")
                and proc.info["cmdline"] is not None
                and "--action" not in proc.info["cmdline"]
            ],
        )
        > 1
    ):
        msg = "Another SchedremManager is running. Program exits."
        sys.exit(msg)

    while True:
        try:
            schedrem = SchedremManager(yaml_path)
            schedrem.run()
        except ValidationError as e:
            logging.debug(e.json(indent=2))
            m = Messenger()
            m.warning(error_message(e.errors()))
        except YAMLError as e:
            msg = f"YAMLError, {e}"
            logging.debug(msg)
            m = Messenger()
            m.warning(msg)
        except FileNotFoundError as e:
            msg = (
                f"{e.__class__.__name__}, "
                f'Config file "{yaml_path}" not found.\nProgram exits.'
            )
            m = Messenger()
            m.error(msg)
            sys.exit(msg)


def main() -> None:
    args = get_args()

    set_logger(args.debug)

    if args.action:
        action_mode(args.action)
    else:
        manager_mode(args.config)


if __name__ == "__main__":
    main()
