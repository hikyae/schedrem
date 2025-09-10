from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    ValidationInfo,
    field_validator,
    model_validator,
)


class WaitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    month: int = 1
    day: int = 1
    hour: int = 0
    minute: int = 0

    @field_validator("month", "day", "hour", "minute")
    @classmethod
    def validate_time(cls, v, info: ValidationInfo):
        field_name = str(info.field_name)
        min_val = {"month": 1, "day": 1, "hour": 0, "minute": 0}[field_name]
        max_val = {"month": 12, "day": 31, "hour": 23, "minute": 59}[field_name]
        if v < min_val or v > max_val:
            msg = f"{field_name} must be between {min_val} and {max_val}."
            raise ValueError(msg)
        return v


class TimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: list[int] | None = None
    month: list[int] | None = None
    day: list[int] | None = None
    weekday: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("weekday", "dow"),
    )
    hour: list[int] | None = None
    minute: list[int] | None = None

    @field_validator("*", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if type(v) in (int, str):
            return [v]
        return v

    @field_validator("month", "day", "hour", "minute")
    @classmethod
    def validate_time(cls, v, info: ValidationInfo):
        field_name = str(info.field_name)
        min_val = {"month": 1, "day": 1, "hour": 0, "minute": 0}[field_name]
        max_val = {"month": 12, "day": 31, "hour": 23, "minute": 59}[field_name]
        if type(v) is list and any(w < min_val or w > max_val for w in v):
            msg = f"{field_name} must be between {min_val} and {max_val}."
            raise ValueError(msg)
        return v

    @field_validator("weekday")
    @classmethod
    def lower_weekday(cls, v):
        """Weekday name matching is case insensitive."""
        if type(v) is list:
            return [w.lower() for w in v]
        return v

    @field_validator("weekday")
    @classmethod
    def weekday_in_weekdaynames(cls, v, info: ValidationInfo):
        """Check weekday is in weekdaynames."""
        if v is None or not info.context:
            return v
        wdn = info.context.get("weekdaynames")
        idx = info.context.get("schedule_idx")
        for w in v:
            if all(w not in aweek for aweek in wdn):
                msg = (
                    f'weekday name "{w}" in schedules.{idx}'
                    f" is not in weekdaynames {wdn}."
                )
                raise ValueError(msg)
        return v


class ActionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yesno: str | None = None
    command: str | None = Field(
        default=None,
        validation_alias=AliasChoices("command", "cmd"),
    )
    message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("message", "msg"),
    )
    sound: str | bool | None = None
    font: str | None = None

    @model_validator(mode="after")
    def validate_actions(self):
        """Check if at least one action is defined."""
        if self.yesno is None and self.command is None and self.message is None:
            msg = "No action specified."
            raise ValueError(msg)
        return self

    @field_validator("sound")
    @classmethod
    def validate_sound(cls, v):
        """Accept WAV only."""
        if type(v) is str and not v.lower().endswith(".wav"):
            msg = "The only accepted format for audio files is WAV."
            raise ValueError(msg)
        return v


class ScheduleConfig(ActionConfig):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(
        default="",
        validation_alias=AliasChoices("description", "desc"),
    )
    time: TimeConfig = TimeConfig()
    wait: WaitConfig | None = None
    # additional delay (in seconds) to be applied to each scheduled time
    delay: NonNegativeFloat = 0.0
    enabled: bool = True

    @field_validator("time")
    @classmethod
    def validate_weekday(cls, v, info: ValidationInfo):
        """Let TimeConfig check weekday is in weekdaynames."""
        if not info.context:
            return v
        wdn = info.context.get("weekdaynames")
        idx = info.context.get("schedule_idx")
        TimeConfig.model_validate(
            dict(v),
            context={"weekdaynames": wdn, "schedule_idx": idx},
        )
        return v


class SchedremConfig(BaseModel):
    disabled: bool = False
    weekdaynames: list[list[str]] = [["mon", "tue", "wed", "thu", "fri", "sat", "sun"]]
    schedules: list[ScheduleConfig] = []
    font: str | None = None

    @field_validator("weekdaynames")
    @classmethod
    def lower_weekdaynames(cls, v):
        """Weekday name matching is case insensitive."""
        return [[x.lower() for x in w] for w in v]

    @field_validator("weekdaynames")
    @classmethod
    def validate_weekdaynames(cls, v):
        """Check that weekdaynames has lists of unique 7 elements."""
        number_of_dow = 7
        for weekdays in v:
            if len(weekdays) > len(set(weekdays)):
                msg = "weekdaynames should have lists of unique elements."
                raise ValueError(msg)
            if len(weekdays) != number_of_dow:
                msg = "weekdaynames should have lists of 7 elements."
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_weekday(self):
        """Let TimeConfig in ScheduleConfig check weekday is in weekdaynames."""
        for i, schedule in enumerate(self.schedules):
            ScheduleConfig.model_validate(
                dict(schedule),
                context={"weekdaynames": self.weekdaynames, "schedule_idx": i},
            )

        return self
