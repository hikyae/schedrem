import logging
import os
import subprocess
import sys
import threading
import wave
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pyaudio

from .config import ActionConfig
from .messagebox import askyesno, showerror, showinfo, showwarning


def program_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def set_logger(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.WARNING,
        format="%(message)s",
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)


def take_action(action: ActionConfig) -> int:
    if action.command and not action.yesno:
        proc = subprocess.Popen(action.command, shell=True)
    if action.yesno:
        logging.debug("yesno: %s\n", action.yesno)
        m = Messenger(action.sound, action.font)
        yes = m.yesno(action.yesno)
        if action.command and yes:
            proc = subprocess.Popen(action.command, shell=True)
        if not yes:
            # action.message won't be shown if action.yesno gets "No" response
            return 1
    if action.message:
        logging.debug("message: %s\n", action.message)
        m = Messenger(action.sound, action.font)
        m.message(action.message)
    if action.command:
        proc.wait()
        return proc.returncode
    return 0


class Messenger:
    prg_dir: Path = program_dir()
    default_sound: Path = prg_dir / "assets/alert.wav"
    icon: Path = prg_dir / "assets/schedrem.ico"

    def __init__(
        self,
        sound: str | bool | None = None,
        font: str | None = None,
    ) -> None:
        self.sound_path: Path | None
        if sound is True:
            self.sound_path = self.default_sound
        elif type(sound) is str:
            self.sound_path = Path(os.path.expandvars(sound)).expanduser()
            if not self.sound_path.exists():
                self.sound_path = self.default_sound
        else:
            self.sound_path = None

        self.font = font
        self.keep: bool = True

    def sing(self) -> None:
        if self.sound_path is None:
            return
        self.keep = True
        with wave.open(str(self.sound_path), "rb") as wf:
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            channels = wf.getnchannels()
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(sampwidth),
                channels=channels,
                rate=framerate,
                output=True,
            )

            chunk = 1024
            while self.keep:
                wf.rewind()
                buffer = wf.readframes(chunk)
                while self.keep and buffer:
                    stream.write(buffer)
                    buffer = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
        p.terminate()

    def start_singing(self) -> None:
        self.keep = True
        self.song_thread = threading.Thread(target=self.sing, daemon=True)
        self.song_thread.start()

    def stop_singing(self) -> None:
        self.keep = False
        self.song_thread.join()

    def message(self, text: str) -> None:
        self.start_singing()
        showinfo("schedrem", text, self.font, self.icon)
        self.stop_singing()

    def yesno(self, text: str) -> bool:
        ans = False
        self.start_singing()
        ans = askyesno("schedrem", text, self.font, self.icon)
        self.stop_singing()
        return ans

    def warning(self, text: str) -> None:
        showwarning("schedrem", text, self.font, self.icon)

    def error(self, text: str) -> None:
        showerror("schedrem", text, self.font, self.icon)


def error_message(errors: list) -> str:
    messages = []
    for error in errors:
        loc = ".".join([str(i) for i in error.get("loc", [])])
        msg = error.get("msg", "")
        ipt = error.get("input")
        message = f"{loc}\n{msg}\ninput: {ipt}"
        messages.append(message)
    return "\n".join(messages)


def get_args() -> Namespace:
    parser = ArgumentParser(description="Task manager and reminder")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file for schedules",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode",
    )
    parser.add_argument(
        "--action",
        type=str,
        help="JSON string to be executed as an action",
    )
    return parser.parse_args()


def get_config_file() -> Path:
    r"""Search and return path to the config file.

    The files are searched in the order specified below and
    only the first one that is found is read.
    Defaults for Linux/macOS:
    "${XDG_CONFIG_HOME}/schedrem/config.yml"
    "${XDG_CONFIG_HOME}/schedrem/config.yaml"
    "${HOME}/.config/schedrem/config.yml"
    "${HOME}/.config/schedrem/config.yaml"
    Defaults for Windows:
    - "%USERPROFILE%\.config\schedrem\config.yml"
    - "%USERPROFILE%\.config\schedrem\config.yaml"
    - "%APPDATA%\schedrem\config.yml"
    - "%APPDATA%\schedrem\config.yaml"
    """
    if os.name == "posix":
        paths = (
            "${XDG_CONFIG_HOME}/schedrem/config.yml",
            "${XDG_CONFIG_HOME}/schedrem/config.yaml",
            "${HOME}/.config/schedrem/config.yml",
            "${HOME}/.config/schedrem/config.yaml",
        )
    elif os.name == "nt":
        paths = (
            "${USERPROFILE}/.config/schedrem/config.yml",
            "${USERPROFILE}/.config/schedrem/config.yaml",
            "${APPDATA}/schedrem/config.yml",
            "${APPDATA}/schedrem/config.yaml",
        )
    else:
        msg = "OS must be either POSIX or NT."
        raise OSError(msg)

    for p in paths:
        path = Path(os.path.expandvars(p)).resolve()
        if path.exists():
            return path

    msg = f"Config file not found in {paths}."
    raise FileNotFoundError(msg)
