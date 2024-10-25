import contextlib
import logging
import os
import subprocess
import sys
import threading
import wave
from pathlib import Path
from tkinter import TclError, Tk, messagebox

import pyaudio

from .config import ActionConfig


def program_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def take_action(action: ActionConfig) -> None:
    if action.command and not action.yesno:
        subprocess.Popen(action.command, shell=True)
    yes = False
    if action.yesno:
        logging.debug("yesno: %s\n", action.yesno)
        m = Messenger(action.sound, action.font)
        yes = m.yesno(action.yesno)
    if action.command and yes:
        subprocess.Popen(action.command, shell=True)
    if action.message:
        logging.debug("message: %s\n", action.message)
        m = Messenger(action.sound, action.font)
        m.message(action.message)


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

    def prepare_root(self) -> None:
        self.root = Tk()
        with contextlib.suppress(TclError):
            self.root.iconbitmap(str(self.icon))
        # make Tk blank window invisible
        self.root.withdraw()
        self.root.attributes("-topmost", True)
        self.root.option_add("*Dialog.msg.font", self.font or "Arial 19")
        self.root.option_add("*Dialog.msg.wrapLength", "800p")

    def sing(self) -> None:
        if self.sound_path is None:
            return
        self.keep = True
        with wave.open(str(self.sound_path), "rb") as wf:
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
        p = pyaudio.PyAudio()
        while self.keep:
            stream = p.open(
                format=p.get_format_from_width(sampwidth),
                channels=channels,
                rate=framerate,
                output=True,
            )
            stream.write(frames)
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
        self.prepare_root()
        self.start_singing()
        messagebox.showinfo("schedrem", text)
        self.stop_singing()
        self.root.destroy()

    def yesno(self, text: str) -> bool:
        self.prepare_root()
        ans = False
        self.start_singing()
        ans = messagebox.askyesno("schedrem", text)
        self.stop_singing()
        self.root.destroy()
        return ans

    def warning(self, text: str) -> None:
        self.prepare_root()
        messagebox.showwarning("schedrem", text)
        self.root.destroy()

    def error(self, text: str) -> None:
        self.prepare_root()
        messagebox.showerror("schedrem", text)
        self.root.destroy()


def error_message(errors: list[dict]) -> str:
    messages = []
    for error in errors:
        loc = ".".join([str(i) for i in error.get("loc", [])])
        msg = error.get("msg", "")
        ipt = error.get("input")
        if type(ipt) is dict and ipt.get("weekdaynames"):
            """SchedremConfig.validate_weekday() returns
            the entire SchedremConfig object, even though
            it only concerns TimeConfig.weekday and SchedremConfig.weekdaynames.
            Consider removing the unnecessary information.
            """
            ipt = ipt.get("weekdaynames")
        else:
            ipt = str(ipt)
        message = f"{loc}\n{msg}\ninput: {ipt}"
        messages.append(message)
    return "\n".join(messages)


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
        path = Path(os.path.expandvars(p))
        if path.exists():
            return path

    msg = f"Config file not found in {paths}."
    raise FileNotFoundError(msg)
