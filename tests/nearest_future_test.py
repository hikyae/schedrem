from datetime import datetime
from typing import cast

from freezegun import freeze_time

from schedrem.config import ScheduleConfig
from schedrem.manager import ScheduleManager

DUMMY_NOW = datetime(2024, 10, 28, 0, 0, 0)
DUMMY_WEEKDAYNAMES = [
    ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    ["月", "火", "水", "木", "金", "土", "日"],
]


def dummy_week_num(weekday: str | list[str] | None) -> int | list[int] | None:
    """According to date.weekday(), monday is 0 and sunday is 6."""
    if type(weekday) is list:
        return cast(list[int], [dummy_week_num(w) for w in weekday])
    for aweek in DUMMY_WEEKDAYNAMES:
        for i, name in enumerate(aweek):
            if weekday == name:
                return i
    return None


@freeze_time(DUMMY_NOW)
def test_case_1():
    schedule = {"time": {"hour": 1}, "message": "test"}
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2024, 10, 28, 1, 0, 0)


@freeze_time(DUMMY_NOW)
def test_case_2():
    schedule = {
        "time": {"hour": 1},
        "message": "test",
        "wait": {"year": 2025, "month": 2},
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2025, 2, 1, 1, 0, 0)


@freeze_time(DUMMY_NOW)
def test_case_3():
    schedule = {
        "time": {"year": [2023, 3000, 3001], "hour": 1, "minute": [5, 10, 20]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(3000, 1, 1, 1, 5, 0)


@freeze_time(DUMMY_NOW)
def test_case_4():
    schedule = {
        "time": {"year": 5000, "month": [2, 3], "hour": 1, "minute": [5, 10, 20]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(5000, 2, 1, 1, 5, 0)


@freeze_time(DUMMY_NOW)
def test_case_5():
    schedule = {
        "time": {
            "year": 5000,
            "month": [2, 3],
            "day": 5,
            "hour": 1,
            "minute": [5, 10, 20],
            "weekday": "Fri",
        },
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) is None


@freeze_time(DUMMY_NOW)
def test_case_6():
    schedule = {
        "time": {
            "year": 5000,
            "month": [2, 3],
            "day": 5,
            "hour": 1,
            "minute": [5, 10, 20],
            "weekday": ["weD", "Fri"],
        },
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(5000, 2, 5, 1, 5)


@freeze_time(DUMMY_NOW)
def test_case_7():
    schedule = {
        "time": {
            "day": 13,
            "weekday": "Fri",
        },
        "wait": {
            "year": 5000,
        },
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(5000, 6, 13, 0, 0)


@freeze_time(DUMMY_NOW)
def test_case_8():
    schedule = {
        "time": {
            "day": 13,
            "weekday": "Fri",
        },
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2024, 12, 13, 0, 0)


@freeze_time(DUMMY_NOW)
def test_case_9():
    schedule = {
        "time": {"month": [10, 12], "minute": [1, 59]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2024, 10, 28, 0, 1)


@freeze_time(DUMMY_NOW)
def test_case_10():
    schedule = {
        "time": {},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2024, 10, 28, 0, 1)


@freeze_time(DUMMY_NOW)
def test_case_11():
    schedule = {
        "time": {},
        "message": "test",
        "wait": {"year": 2025, "month": 2},
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2025, 2, 1, 0, 0)


@freeze_time(DUMMY_NOW)
def test_case_12():
    schedule = {
        "time": {"minute": [3], "dow": "wed"},
        "message": "test",
        "wait": {"year": 2025, "month": 2},
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2025, 2, 5, 0, 3)


@freeze_time(DUMMY_NOW)
def test_case_13():
    schedule = {
        "time": {"year": [9998], "dow": "wed"},
        "message": "test",
        "wait": {"year": 9999, "month": 2},
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) is None


@freeze_time(DUMMY_NOW)
def test_case_14():
    schedule = {
        "time": {"year": [2015], "month": 10, "day": [21]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) is None


@freeze_time(DUMMY_NOW)
def test_case_15():
    schedule = {
        "time": {"year": [2015, 2024, 2025], "month": 10, "minute": [1, 5]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2024, 10, 28, 0, 1)


@freeze_time(DUMMY_NOW)
def test_case_16():
    schedule = {
        "time": {"year": 2025, "month": 10, "dow": ["mon", "金"]},
        "message": "test",
    }
    sch = ScheduleConfig(**schedule)
    schman = ScheduleManager(sch, dummy_week_num, None)
    assert schman.nearest_future(sch.time) == datetime(2025, 10, 3, 0, 0)
