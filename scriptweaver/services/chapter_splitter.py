from __future__ import annotations

import re

from scriptweaver.domain.models import Chapter

# Matches: 第一章 / 第1章 / Chapter 1 / Chapter 1: Title
_CHAPTER_PATTERN = re.compile(
    r"^(?:第[一二三四五六七八九十百千]+章|第\d+章|Chapter\s+\d+)",
    re.MULTILINE,
)


class ChapterSplitterError(ValueError):
    """Raised when chapter splitting fails."""


def split_chapters(text: str) -> list[Chapter]:
    """Split text into chapters by recognised heading patterns.

    Returns a list of Chapter objects with 1-based indexes.
    When no chapter headings are found, the entire text becomes a
    single chapter titled "正文".
    """
    if not text.strip():
        raise ChapterSplitterError("Cannot split empty text")

    matches = list(_CHAPTER_PATTERN.finditer(text))

    if not matches:
        return [
            Chapter(
                index=1,
                title="正文",
                content=text.strip(),
            )
        ]

    chapters: list[Chapter] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        # Extract title — everything from heading to the next newline
        line_end = text.find("\n", start)
        if line_end == -1:
            line_end = len(text)
        title = text[start:line_end].strip()

        content = text[line_end + 1 : end].strip() if line_end < end else ""

        chapters.append(
            Chapter(
                index=i + 1,
                title=title,
                content=content,
            )
        )

    return chapters
