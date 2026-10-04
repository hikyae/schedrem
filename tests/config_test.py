import pytest
from pydantic import ValidationError

from schedrem.config import SchedremConfig, ScheduleConfig


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        ({}, True),
        ({"enabled": True}, True),
        ({"enabled": False}, False),
        ({"disabled": True}, False),
        ({"disabled": False}, True),
    ],
)
def test_global_activation(config, expected):
    assert SchedremConfig(**config).is_enabled is expected


def test_global_activation_flags_are_mutually_exclusive():
    with pytest.raises(ValidationError, match="mutually exclusive"):
        SchedremConfig(enabled=False, disabled=False)


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        ({}, True),
        ({"enabled": True}, True),
        ({"enabled": False}, False),
        ({"disabled": True}, False),
        ({"disabled": False}, True),
    ],
)
def test_schedule_activation(config, expected):
    schedule = ScheduleConfig(message="test", **config)
    assert schedule.is_enabled is expected


def test_schedule_activation_flags_are_mutually_exclusive():
    with pytest.raises(ValidationError, match="mutually exclusive"):
        ScheduleConfig(message="test", enabled=True, disabled=True)


def test_schedule_activation_flags_are_mutually_exclusive_in_global_config():
    with pytest.raises(ValidationError, match="mutually exclusive"):
        SchedremConfig(
            schedules=[{"message": "test", "enabled": False, "disabled": False}],
        )
