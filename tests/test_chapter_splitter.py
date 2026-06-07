"""Tests for chapter splitting logic."""

import pytest

from scriptweaver.services.chapter_splitter import (
    ChapterSplitterError,
    split_chapters,
)


def test_splits_chinese_chapter_headings():
    text = (
        "第一章 密信\n林照收到密信。\n\n"
        "第二章 阻拦\n沈微阻止公开。\n\n"
        "第三章 旧案\n两人发现线索。"
    )
    chapters = split_chapters(text)
    assert len(chapters) == 3
    assert chapters[0].index == 1
    assert chapters[0].title == "第一章 密信"
    assert "林照收到密信" in chapters[0].content
    assert chapters[1].index == 2
    assert chapters[1].title == "第二章 阻拦"
    assert chapters[2].index == 3
    assert chapters[2].title == "第三章 旧案"


def test_splits_english_chapter_headings():
    text = (
        "Chapter 1: The Letter\nContent one.\n\n"
        "Chapter 2: The Block\nContent two."
    )
    chapters = split_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].index == 1
    assert chapters[0].title == "Chapter 1: The Letter"
    assert chapters[1].index == 2


def test_splits_numbered_headings():
    text = (
        "第1章 开始\n第一段内容。\n\n"
        "第2章 继续\n第二段内容。"
    )
    chapters = split_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].index == 1
    assert chapters[1].index == 2


def test_returns_single_chapter_for_no_headings():
    text = "这是一段没有任何章节标题的纯文本内容。"
    chapters = split_chapters(text)
    assert len(chapters) == 1
    assert chapters[0].index == 1
    assert chapters[0].title == "正文"
    assert chapters[0].content.strip() == text.strip()


def test_rejects_empty_text():
    with pytest.raises(ChapterSplitterError, match="empty"):
        split_chapters("")


def test_rejects_whitespace_only_text():
    with pytest.raises(ChapterSplitterError, match="empty"):
        split_chapters("  \n\t  ")


def test_preserves_chapter_content():
    text = "第一章 测试\n第一段很长的内容，包含多个句子。\n还有第二行。"
    chapters = split_chapters(text)
    assert "第一段很长的内容" in chapters[0].content
    assert "第二行" in chapters[0].content


def test_handles_consecutive_newlines():
    text = "第一章 A\n\n\n内容开始。\n\n更多内容。"
    chapters = split_chapters(text)
    assert len(chapters) == 1
    assert "内容开始" in chapters[0].content
