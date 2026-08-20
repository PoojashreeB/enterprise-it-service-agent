import pytest

from app.rag import retriever


# ================================================================
# normalize_text
# ================================================================

def test_normalize_text_lowercases_and_strips_punctuation():
    assert retriever.normalize_text("VPN is Not Connecting!!") == "vpn is not connecting"


def test_normalize_text_collapses_whitespace():
    assert retriever.normalize_text("too   many\n\nspaces") == "too many spaces"


# ================================================================
# extract_keywords
# ================================================================

def test_extract_keywords_removes_stop_words_and_short_words():
    keywords = retriever.extract_keywords("I cannot access my company applications")

    assert "access" in keywords
    assert "company" in keywords
    assert "applications" in keywords
    assert "cannot" not in keywords
    assert "my" not in keywords
    assert "i" not in keywords


# ================================================================
# calculate_score
# ================================================================

def test_calculate_score_rewards_keyword_overlap():
    document = {"content": "The VPN application is not accessible after connecting."}

    score = retriever.calculate_score("VPN application is not accessible", document)

    assert score > 0


def test_calculate_score_penalizes_connection_contradiction():
    connecting_query = "VPN is connected but I cannot access company applications"
    access_document = {
        "content": "Company applications are not accessible even though the VPN is connected."
    }
    connection_document = {
        "content": "The VPN is not connecting. VPN client does not connect."
    }

    access_score = retriever.calculate_score(connecting_query, access_document)
    connection_score = retriever.calculate_score(connecting_query, connection_document)

    assert access_score > connection_score


# ================================================================
# retrieve
# ================================================================

@pytest.fixture()
def sample_documents():
    return [
        {
            "id": "vpn_0",
            "category": "vpn",
            "source": "vpn.txt",
            "content": "VPN is not connecting. VPN client does not connect.",
        },
        {
            "id": "outlook_0",
            "category": "outlook",
            "source": "outlook.txt",
            "content": "Outlook is not opening. Restart Outlook and try again.",
        },
        {
            "id": "irrelevant_0",
            "category": "misc",
            "source": "misc.txt",
            "content": "This document shares no meaningful overlap with any query at all.",
        },
    ]


def test_retrieve_returns_relevant_documents_above_threshold(monkeypatch, sample_documents):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: sample_documents)

    results = retriever.retrieve(query="Outlook is not opening", top_k=5)

    assert any(result["id"] == "outlook_0" for result in results)
    assert all(result["score"] >= retriever.MIN_SCORE for result in results)


def test_retrieve_excludes_low_scoring_documents(monkeypatch, sample_documents):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: sample_documents)

    results = retriever.retrieve(query="Outlook is not opening", top_k=5)

    assert not any(result["id"] == "irrelevant_0" for result in results)


def test_retrieve_respects_top_k(monkeypatch, sample_documents):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: sample_documents)

    results = retriever.retrieve(query="VPN is not connecting", top_k=1)

    assert len(results) <= 1


def test_retrieve_filters_by_category(monkeypatch, sample_documents):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: sample_documents)

    results = retriever.retrieve(
        query="Outlook is not opening",
        top_k=5,
        category="VPN",
    )

    assert all(result["category"] == "vpn" for result in results)
    assert not any(result["id"] == "outlook_0" for result in results)


def test_retrieve_returns_empty_list_when_no_documents(monkeypatch):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: [])

    assert retriever.retrieve(query="anything") == []


def test_retrieve_sorts_results_by_descending_score(monkeypatch, sample_documents):
    monkeypatch.setattr(retriever, "load_knowledge", lambda: sample_documents)

    results = retriever.retrieve(
        query="VPN is connected but I cannot access company applications",
        top_k=5,
    )

    scores = [result["score"] for result in results]
    assert scores == sorted(scores, reverse=True)


# ================================================================
# load_knowledge
# ================================================================

def test_load_knowledge_raises_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(retriever, "KNOWLEDGE_FILE", tmp_path / "does-not-exist.json")

    with pytest.raises(FileNotFoundError):
        retriever.load_knowledge()


def test_load_knowledge_reads_real_data_file():
    documents = retriever.load_knowledge()

    assert isinstance(documents, list)
    assert len(documents) > 0
    assert "content" in documents[0]


# ================================================================
# Integration against the real knowledge base
# ================================================================

@pytest.mark.parametrize(
    "query, category, expected_category",
    [
        ("VPN is connected but I cannot access company applications", "VPN", "vpn"),
        ("Outlook is not opening", "OUTLOOK", "outlook"),
        ("How do I install approved software?", "SOFTWARE_INSTALLATION", "software"),
        ("I forgot my password", "PASSWORD_RESET", "password"),
    ],
)
def test_retrieve_against_real_knowledge_base(query, category, expected_category):
    results = retriever.retrieve(query=query, top_k=3, category=category)

    assert results
    assert results[0]["category"] == expected_category
