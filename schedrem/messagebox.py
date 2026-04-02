#!/usr/bin/env python3
import contextlib
import ctypes
import sys

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox


def set_app_user_model_id(app_id: str) -> None:
    # Only on Windows
    if sys.platform != "win32":
        return

    with contextlib.suppress(Exception):
        # Fail silently on older Windows or unexpected env
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


class KeyBlocker(QObject):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent

    def eventFilter(self, _, event) -> bool:
        if not self.parent.locked:
            return False

        evtype = event.type()
        if evtype == QEvent.KeyPress and event.key() in (
            Qt.Key_Return,
            Qt.Key_Enter,
            Qt.Key_Escape,
            Qt.Key_Space,
        ):
            return True
        return evtype == QEvent.MouseButtonPress


class BlockingMessageBox(QMessageBox):
    def __init__(
        self,
        icon,
        title,
        message,
        font,
        window_icon,
        buttons=QMessageBox.Ok,
    ) -> None:
        super().__init__()

        self.locked = True

        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setIcon(icon)
        self.setWindowIcon(QIcon(str(window_icon)))
        self.setWindowTitle(title)
        self.setText(message)
        self.setStandardButtons(buttons)

        font_family, font_size = self.parse_font(font)

        style = (
            f'QMessageBox {{ font-family: "{font_family}"; font-size: {font_size}pt; }}'
        )
        self.setStyleSheet(style)

        blocker = KeyBlocker(self)
        for btn in self.buttons():
            btn.installEventFilter(blocker)

        QTimer.singleShot(500, lambda: setattr(self, "locked", False))

        self.raise_()
        self.activateWindow()

    def parse_font(self, font: str | None) -> tuple[str, str]:
        default = ("Arial", "15")
        if type(font) is not str:
            return default
        parts = font.rsplit(maxsplit=1)
        if len(parts) == 2:  # noqa: PLR2004
            return tuple(parts)  # type: ignore[return-value]
        return default


def ensure_app(icon) -> None:
    set_app_user_model_id("app.schedrem.messagebox")
    app = QApplication.instance() or QApplication()
    app.setWindowIcon(QIcon(str(icon)))


def _show(
    icon, title, message, font, window_icon, buttons=QMessageBox.Ok
) -> BlockingMessageBox:
    ensure_app(window_icon)
    return BlockingMessageBox(icon, title, message, font, window_icon, buttons).exec()


def showinfo(title, message, font, window_icon):
    _show(
        QMessageBox.Information,
        title,
        message,
        font,
        window_icon,
        buttons=QMessageBox.Ok,
    )


def showwarning(title, message, font, window_icon):
    _show(
        QMessageBox.Warning, title, message, font, window_icon, buttons=QMessageBox.Ok
    )


def showerror(title, message, font, window_icon):
    _show(
        QMessageBox.Critical, title, message, font, window_icon, buttons=QMessageBox.Ok
    )


def askyesno(title, message, font, window_icon):
    return (
        _show(
            QMessageBox.Question,
            title,
            message,
            font,
            window_icon,
            buttons=QMessageBox.Yes | QMessageBox.No,
        )
        == QMessageBox.Yes
    )
