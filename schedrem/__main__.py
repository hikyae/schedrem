import argparse
import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError
from yaml import YAMLError

from .config import ActionConfig
from .manager import SchedremManager
from .util import Messenger, error_message, get_config_file, take_action


def main() -> None:
    parser = argparse.ArgumentParser(description="Task manager and reminder")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file for schedules",
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        help="Debug mode",
    )
    parser.add_argument(
        "--action",
        type=str,
        help="JSON string to be executed as an action",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(message)s",
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)

    if args.action:
        try:
            action = ActionConfig(**json.loads(args.action))
            take_action(action)
        except Exception as e:
            msg = f"{e.__class__.__name__}, {e}"
            m = Messenger()
            m.warning(msg)
        sys.exit()

    if args.config:
        yaml_path = Path(args.config).resolve()
    else:
        try:
            yaml_path = get_config_file()
        except Exception as e:
            msg = f"{e.__class__.__name__}, {e}\nProgram exits."
            m = Messenger()
            m.error(msg)
            sys.exit(msg)

    logging.debug("config path: %s\n", yaml_path)

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


if __name__ == "__main__":
    main()
