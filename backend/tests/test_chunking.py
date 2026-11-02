import pytest

from docagent.ingest.chunking import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n ", size=100, overlap=10) == []


def test_short_text_is_one_chunk():
    assert chunk_text("hello   world\n", size=100, overlap=10) == ["hello world"]


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_text(text, size=100, overlap=30)
    assert all(len(c) <= 100 for c in chunks)
    for a, b in zip(chunks, chunks[1:], strict=False):
        assert a.split()[-1] in b.split()
    words = set(text.split())
    assert all(w in words for c in chunks for w in c.split())
    assert chunks[-1].endswith("word199")


def test_long_word_still_progresses():
    chunks = chunk_text("x" * 250, size=100, overlap=20)
    assert [len(c) for c in chunks] == [100, 100, 90]


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_text("abc", size=10, overlap=10)
