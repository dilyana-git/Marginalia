from sqlmodel import Field, SQLModel


class AppSettings(SQLModel, table=True):
    __tablename__ = "appsettings"

    id: int | None = Field(default=1, primary_key=True)
    reader_name: str = Field(default="")
    reader_interests: str = Field(default="")
    recipient_email: str | None = None
    timezone: str = Field(default="Europe/Sofia")
    send_schedule_cron: str = Field(default="0 6 * * *")
    newsletter_enabled: bool = Field(default=True)
    max_per_source: int = Field(default=6)
    lookback_days: int = Field(default=7)
    model_name: str = Field(default="claude-haiku-4-5")
