from pydantic import BaseModel


class SettingsRead(BaseModel):
    id: int
    reader_name: str
    reader_interests: str
    recipient_email: str | None
    timezone: str
    send_schedule_cron: str
    newsletter_enabled: bool
    max_per_source: int
    lookback_days: int
    model_name: str


class SettingsUpdate(BaseModel):
    reader_name: str | None = None
    reader_interests: str | None = None
    recipient_email: str | None = None
    timezone: str | None = None
    send_schedule_cron: str | None = None
    newsletter_enabled: bool | None = None
    max_per_source: int | None = None
    lookback_days: int | None = None
    model_name: str | None = None


class SettingsCreate(BaseModel):
    reader_name: str = ""
    reader_interests: str = ""
    recipient_email: str | None = None
    timezone: str = "Europe/Sofia"
    send_schedule_cron: str = "0 6 * * *"
    newsletter_enabled: bool = True
    max_per_source: int = 6
    lookback_days: int = 7
    model_name: str = "claude-haiku-4-5"
