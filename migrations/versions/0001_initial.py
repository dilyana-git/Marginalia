"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2025-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "region",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("qualifier", sa.String(), nullable=True),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("rank_note", sa.String(), nullable=True),
        sa.Column("anchor", sa.Text(), nullable=True),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ordinal"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_region_ordinal", "region", ["ordinal"])
    op.create_index("ix_region_name", "region", ["name"])

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tag_name", "tag", ["name"])

    op.create_table(
        "work",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("subtitle", sa.String(), nullable=True),
        sa.Column("authors", sa.JSON(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column(
            "region_id",
            sa.Integer(),
            sa.ForeignKey("region.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("isbn", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("date_added", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_started", sa.Date(), nullable=True),
        sa.Column("date_finished", sa.Date(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("is_start_here", sa.Boolean(), nullable=False),
        sa.Column("seed_origin", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_work_title", "work", ["title"])
    op.create_index("ix_work_region_id", "work", ["region_id"])
    op.create_index("ix_work_status", "work", ["status"])
    op.create_index("ix_work_tier", "work", ["tier"])
    op.create_index("ix_work_format", "work", ["format"])

    op.create_table(
        "worktag",
        sa.Column(
            "work_id",
            sa.Integer(),
            sa.ForeignKey("work.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tag.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "readinglist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_readinglist_name", "readinglist", ["name"])

    op.create_table(
        "listitem",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "list_id",
            sa.Integer(),
            sa.ForeignKey("readinglist.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "work_id",
            sa.Integer(),
            sa.ForeignKey("work.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.UniqueConstraint("list_id", "work_id"),
    )
    op.create_index("ix_listitem_list_id", "listitem", ["list_id"])
    op.create_index("ix_listitem_work_id", "listitem", ["work_id"])

    op.create_table(
        "journalentry",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "work_id",
            sa.Integer(),
            sa.ForeignKey("work.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("page_or_location", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_journalentry_work_id", "journalentry", ["work_id"])
    op.create_index("ix_journalentry_kind", "journalentry", ["kind"])

    op.create_table(
        "journaltag",
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("journalentry.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tag.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "feed",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column(
            "region_id",
            sa.Integer(),
            sa.ForeignKey("region.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(), nullable=True),
        sa.Column("seed_origin", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_feed_url", "feed", ["url"])
    op.create_index("ix_feed_region_id", "feed", ["region_id"])

    op.create_table(
        "newsletterrun",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("items_count", sa.Integer(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=True),
        sa.Column("intro_text", sa.Text(), nullable=True),
        sa.Column("error_log", sa.Text(), nullable=True),
    )

    op.create_table(
        "newsletteritem",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "feed_id",
            sa.Integer(),
            sa.ForeignKey("feed.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("link", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("claude_blurb", sa.Text(), nullable=True),
        sa.Column("is_highlight", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "saved_work_id",
            sa.Integer(),
            sa.ForeignKey("work.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "sent_in_run_id",
            sa.Integer(),
            sa.ForeignKey("newsletterrun.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("feed_id", "external_id"),
    )
    op.create_index("ix_newsletteritem_feed_id", "newsletteritem", ["feed_id"])
    op.create_index("ix_newsletteritem_external_id", "newsletteritem", ["external_id"])
    op.create_index("ix_newsletteritem_status", "newsletteritem", ["status"])

    op.create_table(
        "appsettings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("reader_name", sa.String(), nullable=False),
        sa.Column("reader_interests", sa.Text(), nullable=False),
        sa.Column("recipient_email", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("send_schedule_cron", sa.String(), nullable=False),
        sa.Column("newsletter_enabled", sa.Boolean(), nullable=False),
        sa.Column("max_per_source", sa.Integer(), nullable=False),
        sa.Column("lookback_days", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("appsettings")
    op.drop_table("newsletteritem")
    op.drop_table("newsletterrun")
    op.drop_table("feed")
    op.drop_table("journaltag")
    op.drop_table("journalentry")
    op.drop_table("listitem")
    op.drop_table("readinglist")
    op.drop_table("worktag")
    op.drop_table("work")
    op.drop_table("tag")
    op.drop_table("region")
