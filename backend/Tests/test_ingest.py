import json

import pytest

from app.rag import ingest


# ================================================================
# chunk_text
# ================================================================

def test_chunk_text_returns_empty_list_for_blank_input():
    assert ingest.chunk_text("") == []
    assert ingest.chunk_text("   \n  ") == []


def test_chunk_text_keeps_a_single_small_section_as_one_chunk():
    text = "A short knowledge article that easily fits in one chunk."

    chunks = ingest.chunk_text(text)

    assert chunks == [text]


def test_chunk_text_merges_small_sections_until_the_size_limit():
    section_a = "A" * 100
    section_b = "B" * 100
    text = section_a + "\n" + ("-" * 25) + "\n" + section_b

    chunks = ingest.chunk_text(text)

    assert len(chunks) == 1
    assert section_a in chunks[0]
    assert section_b in chunks[0]


def test_chunk_text_splits_once_the_size_limit_is_exceeded():
    section_a = "A" * (ingest.CHUNK_SIZE - 10)
    section_b = "B" * (ingest.CHUNK_SIZE - 10)
    text = section_a + "\n" + ("-" * 25) + "\n" + section_b

    chunks = ingest.chunk_text(text)

    assert len(chunks) == 2
    assert chunks[0] == section_a
    assert chunks[1] == section_b


def test_chunk_text_splits_an_oversized_single_section_by_line():
    long_line = "x" * 50
    lines = [long_line] * (ingest.CHUNK_SIZE // 51 + 5)
    text = "\n".join(lines)

    chunks = ingest.chunk_text(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= ingest.CHUNK_SIZE
    # No line is lost across the split.
    assert "\n".join(chunks).count(long_line) == len(lines)


# ================================================================
# ingest_knowledge
# ================================================================

def test_ingest_knowledge_raises_when_knowledge_dir_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "KNOWLEDGE_DIR", tmp_path / "does-not-exist")
    monkeypatch.setattr(ingest, "OUTPUT_FILE", tmp_path / "out" / "knowledge.json")

    with pytest.raises(FileNotFoundError):
        ingest.ingest_knowledge()


def test_ingest_knowledge_raises_when_no_txt_files(monkeypatch, tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "notes.md").write_text("not a txt file", encoding="utf-8")

    monkeypatch.setattr(ingest, "KNOWLEDGE_DIR", knowledge_dir)
    monkeypatch.setattr(ingest, "OUTPUT_FILE", tmp_path / "out" / "knowledge.json")

    with pytest.raises(FileNotFoundError):
        ingest.ingest_knowledge()


def test_ingest_knowledge_writes_expected_json(monkeypatch, tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    vpn_dir = knowledge_dir / "vpn"
    vpn_dir.mkdir(parents=True)
    section_a = "First section about VPN issues. " + ("A" * (ingest.CHUNK_SIZE - 50))
    section_b = "Second section with more VPN guidance."
    (vpn_dir / "vpn_troubleshooting.txt").write_text(
        section_a + "\n" + ("-" * 25) + "\n" + section_b,
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "knowledge.json"
    monkeypatch.setattr(ingest, "KNOWLEDGE_DIR", knowledge_dir)
    monkeypatch.setattr(ingest, "OUTPUT_FILE", output_file)

    ingest.ingest_knowledge()

    assert output_file.exists()
    records = json.loads(output_file.read_text(encoding="utf-8"))

    assert len(records) == 2
    assert records[0]["id"] == "vpn_0"
    assert records[0]["category"] == "vpn"
    assert records[0]["source"] == "vpn_troubleshooting.txt"
    assert records[0]["content"] == section_a
    assert records[1]["id"] == "vpn_1"
    assert records[1]["content"] == section_b
