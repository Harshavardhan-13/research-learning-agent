"""Post-model enforcement for word limits and grounded source links."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Final

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types

from .policy import MAX_RESPONSE_WORDS

_MAX_SOURCES: Final = 4
_WORD_PATTERN: Final = re.compile(r"\S+")
_SENTENCE_END_PATTERN: Final = re.compile(r"[.!?](?=\s|$)")


@dataclass(frozen=True, slots=True)
class GroundedSource:
    """A source link returned by Google Search grounding metadata."""

    title: str
    uri: str


def count_words(text: str) -> int:
    """Count display words using whitespace boundaries."""
    return len(_WORD_PATTERN.findall(text))


def _truncate_words(text: str, limit: int) -> tuple[str, bool]:
    matches = list(_WORD_PATTERN.finditer(text))
    if len(matches) <= limit:
        return text.strip(), False
    if limit <= 0:
        return "", True

    candidate = text[: matches[limit - 1].end()].rstrip()
    sentence_ends = list(_SENTENCE_END_PATTERN.finditer(candidate))
    if sentence_ends:
        last_end = sentence_ends[-1].end()
        if count_words(candidate[:last_end]) >= max(1, limit * 3 // 5):
            return candidate[:last_end].rstrip(), True
    return candidate + "…", True

def _remove_repeated_prefix(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    probe = stripped[:80]
    if len(probe) < 40:
        return stripped, False

    repeated_at = stripped.find(probe, len(probe))
    if repeated_at == -1:
        return stripped, False
    return stripped[:repeated_at].rstrip(), True

def _strip_generated_source_section(text: str) -> tuple[str, bool]:
    kept_lines: list[str] = []
    skipping_sources = False
    removed = False

    for line in text.splitlines():
        simplified = line.strip().strip("*# ").casefold().rstrip(":")
        is_source_heading = simplified in {
            "sources",
            "resources",
            "best sources",
            "best resources",
        } or simplified.startswith(("sources for ", "resources for "))
        if is_source_heading:
            skipping_sources = True
            removed = True
            continue

        stripped = line.strip()
        if skipping_sources:
            if not stripped or re.match(r"(?:[-*+]|\d+[.)])\s", stripped):
                continue
            skipping_sources = False
        kept_lines.append(line)

    return "\n".join(kept_lines).strip(), removed




def _clean_title(title: str) -> str:
    compact = " ".join(title.split()) or "Source"
    shortened, _ = _truncate_words(compact, 10)
    return shortened.replace("[", "").replace("]", "")


def format_grounded_response(
    text: str,
    sources: tuple[GroundedSource, ...],
    max_words: int = MAX_RESPONSE_WORDS,
) -> tuple[str, bool]:
    """Append verified links and enforce the complete-response word ceiling."""
    text, duplicate_removed = _remove_repeated_prefix(text)
    text, source_section_removed = _strip_generated_source_section(text)
    normalized_text = re.sub(r"(?<!\.)\.\.(?!\.)", ".", text)
    punctuation_normalized = normalized_text != text
    text = normalized_text
    changed = duplicate_removed or source_section_removed or punctuation_normalized
    unique_sources: list[GroundedSource] = []
    seen_uris: set[str] = set()
    for source in sources:
        if not source.uri or source.uri in seen_uris:
            continue
        seen_uris.add(source.uri)
        unique_sources.append(source)
        if len(unique_sources) == _MAX_SOURCES:
            break

    if unique_sources:
        source_lines = ["Sources (Google Search):"]
        source_lines.extend(
            f"- [{_clean_title(source.title)}]({source.uri})"
            for source in unique_sources
        )
    else:
        source_lines = [
            "Source verification unavailable: Google Search returned no link metadata."
        ]

    source_block = "\n".join(source_lines)
    body_budget = max_words - count_words(source_block)
    body, truncated = _truncate_words(text, body_budget)
    response = f"{body}\n\n{source_block}" if body else source_block
    return response, truncated or changed


def _grounded_sources(llm_response: LlmResponse) -> tuple[GroundedSource, ...]:
    metadata = llm_response.grounding_metadata
    if metadata is None or not metadata.grounding_chunks:
        return ()

    sources: list[GroundedSource] = []
    for chunk in metadata.grounding_chunks:
        web = chunk.web
        if web is None or not web.uri:
            continue
        sources.append(GroundedSource(title=web.title or "Source", uri=web.uri))
    return tuple(sources)


def enforce_grounded_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Return a bounded final response while preserving grounding metadata."""
    del callback_context
    if llm_response.error_message or not llm_response.content:
        return None

    visible_parts = [
        part
        for part in llm_response.content.parts or []
        if part.text and not part.thought
    ]
    if not visible_parts:
        return None

    original_text = "\n".join(part.text for part in visible_parts if part.text)
    response_text, truncated = format_grounded_response(
        original_text,
        _grounded_sources(llm_response),
    )
    updated = llm_response.model_copy(deep=True)
    updated.content = types.Content(
        role=llm_response.content.role or "model",
        parts=[types.Part(text=response_text)],
    )

    logging.getLogger("research_agent").info(
        "response_enforced",
        extra={
            "context": {
                "source_count": len(_grounded_sources(llm_response)),
                "word_count": count_words(response_text),
                "truncated": truncated,
            }
        },
    )
    return updated
