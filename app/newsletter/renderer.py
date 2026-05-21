"""Render newsletter as HTML and plain-text."""

from datetime import UTC, datetime

from app.models import Feed, NewsletterItem, Region

_CREAM = "#FDFBF7"
_TEAL = "#2A7F7F"
_DARK = "#2C2C2C"
_MID = "#6B6B6B"
_LIGHT_BORDER = "#E8E3DC"


def _html_item(item: NewsletterItem, blurb: str | None, is_highlight: bool) -> str:
    highlight_bar = (  # noqa: E501
        f'style="border-left: 3px solid {_TEAL}; padding-left: 12px;"' if is_highlight else ""
    )
    blurb_html = (
        f'<p style="color:{_MID};font-size:13px;margin:4px 0 0;">{blurb}</p>' if blurb else ""
    )
    link_html = (
        f'<a href="{item.link}" style="color:{_TEAL};text-decoration:none;font-weight:600;">'
        f"{item.title}</a>"
        if item.link
        else f"<strong>{item.title}</strong>"
    )
    return f"""
    <div {highlight_bar} style="margin-bottom:16px;">
      <p style="margin:0;">{link_html}</p>
      <p style="color:{_MID};font-size:12px;margin:2px 0;">{item.snippet[:200]}</p>
      {blurb_html}
    </div>"""


def render_html(
    items: list[NewsletterItem],
    feeds_by_id: dict[int, Feed],
    regions_by_id: dict[int, Region | None],
    highlight_ids: set[int],
    blurbs: dict[int, str],
    intro: str,
    run_date: datetime | None = None,
) -> str:
    date_str = (run_date or datetime.now(UTC)).strftime("%A, %-d %B %Y")

    # Group by region (None = cross-cutting)
    by_region: dict[str, list[NewsletterItem]] = {}
    for item in items:
        feed = feeds_by_id.get(item.feed_id)
        region = regions_by_id.get(feed.region_id) if feed and feed.region_id else None
        section = region.name if region else "Cross-cutting"
        by_region.setdefault(section, []).append(item)

    # Highlights box
    highlights = [i for i in items if i.id in highlight_ids]
    highlights_html = ""
    if highlights:
        hl_links = "".join(
            f'<li><a href="{i.link}" style="color:{_TEAL};">{i.title}</a></li>'
            for i in highlights
            if i.link
        )
        highlights_html = f"""
        <div style="background:#EAF5F5;border-radius:6px;padding:16px;margin-bottom:24px;">
          <h3 style="color:{_TEAL};margin:0 0 8px;">Today's highlights</h3>
          <ul style="margin:0;padding-left:20px;">{hl_links}</ul>
        </div>"""

    # Sections
    sections_html = ""
    for section_name, section_items in sorted(by_region.items()):
        items_html = "".join(
            _html_item(i, blurbs.get(i.id), i.id in highlight_ids) for i in section_items  # type: ignore[arg-type]
        )
        h2_style = (  # noqa: E501
            f"color:{_TEAL};border-bottom:1px solid {_LIGHT_BORDER};"
            "padding-bottom:6px;font-size:16px;"
        )
        sections_html += f"""
        <h2 style="{h2_style}">{section_name}</h2>
        {items_html}"""

    intro_html = (
        f'<p style="color:{_DARK};font-size:15px;line-height:1.6;margin-bottom:24px;">'
        f"{intro}</p>"
        if intro
        else ""
    )

    body_style = (
        f"background:{_CREAM};font-family:Georgia,serif;color:{_DARK};"
        "max-width:640px;margin:0 auto;padding:24px;"
    )
    footer_style = (
        f"border-top:1px solid {_LIGHT_BORDER};margin-top:32px;"
        f"padding-top:12px;font-size:11px;color:{_MID};"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Marginalia — {date_str}</title></head>
<body style="{body_style}">
  <header style="border-bottom:2px solid {_TEAL};margin-bottom:24px;padding-bottom:12px;">
    <h1 style="color:{_TEAL};font-size:22px;margin:0;">Marginalia</h1>
    <p style="color:{_MID};font-size:13px;margin:4px 0 0;">{date_str}</p>
  </header>
  {intro_html}
  {highlights_html}
  {sections_html}
  <footer style="{footer_style}">
    Your personal reading digest. {len(items)} items from {len(by_region)} regions.
  </footer>
</body>
</html>"""


def render_plaintext(
    items: list[NewsletterItem],
    feeds_by_id: dict[int, Feed],
    regions_by_id: dict[int, Region | None],
    highlight_ids: set[int],
    blurbs: dict[int, str],
    intro: str,
    run_date: datetime | None = None,
) -> str:
    date_str = (run_date or datetime.now(UTC)).strftime("%A, %-d %B %Y")
    lines = [f"MARGINALIA — {date_str}", "=" * 50, ""]

    if intro:
        lines += [intro, ""]

    # Highlights
    highlights = [i for i in items if i.id in highlight_ids]
    if highlights:
        lines += ["TODAY'S HIGHLIGHTS", "-" * 20]
        for i in highlights:
            lines.append(f"• {i.title}")
            if i.link:
                lines.append(f"  {i.link}")
        lines.append("")

    # Sections
    by_region: dict[str, list[NewsletterItem]] = {}
    for item in items:
        feed = feeds_by_id.get(item.feed_id)
        region = regions_by_id.get(feed.region_id) if feed and feed.region_id else None
        section = region.name if region else "Cross-cutting"
        by_region.setdefault(section, []).append(item)

    for section_name, section_items in sorted(by_region.items()):
        lines += [section_name.upper(), "-" * len(section_name)]
        for item in section_items:
            lines.append(f"\n{item.title}")
            if item.link:
                lines.append(item.link)
            if blurbs.get(item.id):
                lines.append(blurbs[item.id])  # type: ignore[index]
            lines.append(item.snippet[:150] + "…" if len(item.snippet) > 150 else item.snippet)
        lines.append("")

    return "\n".join(lines)
