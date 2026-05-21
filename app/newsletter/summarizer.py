"""Call Claude to generate intro text and per-item blurbs."""

from app.logging import get_logger
from app.models import NewsletterItem

log = get_logger("newsletter.summarizer")

_MAX_ITEMS_FOR_PROMPT = 30


def _build_prompt(reader_name: str, reader_interests: str, items: list[NewsletterItem]) -> str:
    items_text = "\n\n".join(
        f"[{i + 1}] {item.title}\n{item.snippet[:300]}" for i, item in enumerate(items)
    )
    return f"""You are writing a personalised daily reading digest for {reader_name}, {reader_interests}.

Below are up to {len(items)} items from their curated RSS feeds.

For each item, write a single sentence (max 25 words) that tells {reader_name} why this specific item is worth their time given their interests. Be specific, not generic. Do not use the word "discover".

Then choose up to 3 item numbers that are the strongest highlights.

Finally, write a 2-3 sentence introductory paragraph for today's digest.

Respond in this exact JSON format:
{{
  "intro": "...",
  "highlights": [1, 2],
  "blurbs": {{
    "1": "...",
    "2": "...",
    ...
  }}
}}

Items:
{items_text}"""


def summarize(
    items: list[NewsletterItem],
    reader_name: str,
    reader_interests: str,
    model_name: str,
    api_key: str,
) -> tuple[str, list[int], dict[int, str]]:
    """Return (intro, highlight_item_ids, {item_id: blurb})."""
    if not api_key:
        log.warning("ANTHROPIC_API_KEY unset — skipping summarisation")
        return "", [], {}

    if not items:
        return "", [], {}

    import anthropic
    import json

    client = anthropic.Anthropic(api_key=api_key)
    prompt_items = items[:_MAX_ITEMS_FOR_PROMPT]

    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=2048,
            messages=[{"role": "user", "content": _build_prompt(reader_name, reader_interests, prompt_items)}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(raw)

        intro: str = data.get("intro", "")
        highlight_indices: list[int] = [int(x) for x in data.get("highlights", [])]
        blurbs_by_index: dict[str, str] = data.get("blurbs", {})

        # Map from 1-based index to real item id
        highlight_ids = [
            prompt_items[i - 1].id
            for i in highlight_indices
            if 1 <= i <= len(prompt_items) and prompt_items[i - 1].id is not None
        ]
        blurbs_by_id = {
            prompt_items[int(k) - 1].id: v
            for k, v in blurbs_by_index.items()
            if k.isdigit() and 1 <= int(k) <= len(prompt_items) and prompt_items[int(k) - 1].id is not None
        }

        log.info("summarisation complete", items=len(prompt_items), highlights=len(highlight_ids))
        return intro, highlight_ids, blurbs_by_id

    except Exception as exc:
        log.warning("summarisation failed", error=str(exc))
        return "", [], {}
