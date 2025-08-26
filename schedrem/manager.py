import asyncio
import logging
import subprocess
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import psutil
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from yaml import safe_load

from .config import SchedremConfig, ScheduleConfig, TimeConfig


class SchedremManager:
    def __init__(self, yaml_path: Path) -> None:
        self.coros: list = []
        self.tasks: list = []
        self.observer = Observer()
        self.observer.schedule(
            SchedremEventHandler(yaml_path, self),
            str(yaml_path.resolve().parent),
            recursive=False,
        )
        self.config = SchedremConfig(**self.load_yaml(yaml_path))
        if self.config.disabled:
            logging.debug("Schedrem is disabled.\n")
            # terminate all existing action processes when disabled
            for proc in psutil.process_iter(["name", "cmdline"]):
                try:
                    name = proc.info["name"]
                    cmdline = proc.info["cmdline"]
                    if (
                        name in ("schedrem", "schedrem.exe")
                        and cmdline is not None
                        and "--action" in cmdline
                    ):
                        proc.terminate()
                except Exception as e:
                    logging.debug("Failed to terminate process: %s", e)

        else:
            self.set_schedules()

    def load_yaml(self, yaml_path: Path) -> dict:
        with yaml_path.open(encoding="utf-8", errors="replace") as file:
            return safe_load(file) or {}

    def week_nums(self, weekdays: list[str] | None) -> list[int] | None:
        """Convert a list of weekday names to their corresponding weekday numbers.

        According to date.weekday(), Monday is 0 and Sunday is 6.
        """
        if not weekdays:
            return None

        name_to_index: dict[str, int] = {
            name: idx
            for idx, names in enumerate(zip(*self.config.weekdaynames, strict=False))
            for name in names
        }
        return [name_to_index[w] for w in weekdays if w in name_to_index]

    def set_schedules(self) -> None:
        self.sched_mans = [
            ScheduleManager(sch, self.week_nums, self.config.font)
            for sch in self.config.schedules
        ]
        self.coros = [sched.standby for sched in self.sched_mans]

    async def cancel_awaiter(self) -> None:
        """Just a sleep loop waiting for cancellation."""
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    def run(self) -> None:
        logging.debug("weekdaynames: %s\n", self.config.weekdaynames)

        async def create_tasks() -> None:
            async with asyncio.TaskGroup() as tg:
                self.tasks = [tg.create_task(coro()) for coro in self.coros]
                self.tasks.append(tg.create_task(self.cancel_awaiter()))

        self.observer.start()
        asyncio.run(create_tasks())
        logging.debug("Tasks have been cancelled!\n")
        self.observer.stop()
        self.observer.join()


class ScheduleManager:
    def __init__(
        self,
        sconf: ScheduleConfig,
        week_nums: Callable,
        font: str | None,
    ) -> None:
        self.sconf = sconf
        self.sconf.font = self.sconf.font or font
        self.week_nums = week_nums

    async def standby(self) -> None:
        while True:
            """No time key should be set in a schedule
            if it should be triggered every minute.
            It means the same as * * * * * in crontab.
            """
            if not self.sconf.enabled:
                return
            nexttime = self.nearest_future(self.sconf.time)
            if not nexttime:
                return
            nexttime += timedelta(seconds=self.sconf.delay)
            waittime = (nexttime - datetime.now()).total_seconds()
            logging.debug(self.sconf)
            logging.debug(nexttime)
            logging.debug("%s seconds left\n", waittime)

            try:
                await asyncio.sleep(waittime)
                while datetime.now() < nexttime:
                    """Adjust the gap between monotonic and real-time clocks
                    if waittime is not enough for nexttime.
                    """
                    await asyncio.sleep(0.1)
                action_arg = self.sconf.model_dump_json(
                    include={
                        "yesno",
                        "command",
                        "message",
                        "sound",
                        "font",
                    },
                )
                subprocess.Popen(["schedrem", "--action", action_arg])
            except asyncio.CancelledError:
                break

    def nearest_future(self, tconf: TimeConfig) -> datetime | None:
        now = datetime.now().replace(second=0, microsecond=0)
        now += timedelta(minutes=1)  # trigger from next minute

        if self.sconf.wait:
            candidate = datetime(**self.sconf.wait.model_dump())
            candidate = max(candidate, now)
        else:
            candidate = now

        if tconf.year:
            if candidate.year > max(tconf.year):
                return None
            if candidate.year not in tconf.year:
                candidate = datetime(
                    min([y for y in tconf.year if y > candidate.year]),
                    min(tconf.month) if tconf.month else 1,
                    min(tconf.day) if tconf.day else 1,
                )

        if (
            tconf.month
            and candidate.month not in tconf.month
            or tconf.day
            and candidate.day not in tconf.day
        ):
            delta = {"days": 1}
            candidate = datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                min(tconf.hour) if tconf.hour else 0,
                min(tconf.minute) if tconf.minute else 0,
            )
        else:
            delta = {"minutes": 1}

        def time_match(candi: int, setting: list[int] | None) -> bool:
            return not setting or candi in setting

        while not tconf.year or min(tconf.year) <= candidate.year <= max(tconf.year):
            if (
                time_match(candidate.year, tconf.year)
                and time_match(candidate.month, tconf.month)
                and time_match(candidate.day, tconf.day)
                and time_match(candidate.hour, tconf.hour)
                and time_match(candidate.minute, tconf.minute)
                and time_match(candidate.weekday(), self.week_nums(tconf.weekday))
            ):
                return candidate
            candidate += timedelta(**delta)

        return None


class SchedremEventHandler(FileSystemEventHandler):
    def __init__(self, yaml_path: Path, app_manager: SchedremManager) -> None:
        self.yaml_path = yaml_path
        self.app_manager = app_manager

    def is_yaml_path(self, path: str) -> bool:
        return Path(path) == self.yaml_path

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.event_type in [
            "modified",
            "moved",
            "deleted",
        ] and self.is_yaml_path(str(event.src_path)):
            for task in self.app_manager.tasks:
                task.cancel()
