from pathlib import Path
import json
import re


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_FILE = (
    BASE_DIR
    / "data"
    / "knowledge.json"
)

DEFAULT_TOP_K = 3

MIN_SCORE = 3


# ============================================================
# Category Mapping
# ============================================================

CATEGORY_MAP = {
    "VPN": "vpn",
    "OUTLOOK": "outlook",
    "SOFTWARE_INSTALLATION": "software",
    "PASSWORD_RESET": "password",
}


# ============================================================
# Load Knowledge
# ============================================================

def load_knowledge():

    if not KNOWLEDGE_FILE.exists():

        raise FileNotFoundError(
            f"Knowledge file not found: "
            f"{KNOWLEDGE_FILE}"
        )

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# Normalize Text
# ============================================================

def normalize_text(text):

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    return " ".join(
        text.split()
    )


# ============================================================
# Extract Keywords
# ============================================================

def extract_keywords(text):

    normalized = normalize_text(text)

    words = normalized.split()

    stop_words = {
        "the",
        "is",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "for",
        "my",
        "i",
        "cannot",
        "can",
        "not",
        "but",
        "with",
        "in",
        "on",
        "it",
        "this",
        "that",
        "are",
        "be",
        "was",
        "were",
        "do",
        "does",
        "how",
        "what",
        "please",
        "me",
    }

    return {
        word
        for word in words
        if word not in stop_words
        and len(word) > 2
    }


# ============================================================
# Calculate Relevance Score
# ============================================================

def calculate_score(
    query,
    document
):

    query_normalized = normalize_text(
        query
    )

    document_text = normalize_text(
        document.get(
            "content",
            ""
        )
    )

    query_keywords = extract_keywords(
        query
    )

    document_keywords = extract_keywords(
        document_text
    )

    score = 0

    # --------------------------------------------------------
    # Keyword overlap
    # --------------------------------------------------------

    overlap = (
        query_keywords
        &
        document_keywords
    )

    score += len(overlap)

    # --------------------------------------------------------
    # Phrase matching
    # --------------------------------------------------------

    query_phrases = [

        "vpn is connected",

        "company applications",

        "cannot access company applications",

        "outlook is not opening",

        "cannot send emails",

        "outlook is not syncing",

        "software installation",

        "install approved software",

        "forgot my password",

        "password has expired",

    ]

    for phrase in query_phrases:

        if phrase in query_normalized:

            if phrase in document_text:

                score += 5

    # --------------------------------------------------------
    # Important terms
    # --------------------------------------------------------

    important_terms = {

        "connected": 2,

        "disconnecting": 2,

        "applications": 2,

        "accessible": 2,

        "opening": 2,

        "emails": 2,

        "syncing": 2,

        "installation": 2,

        "password": 2,

        "expired": 2,

        "forgot": 2,

    }

    for term, weight in important_terms.items():

        if term in query_keywords:

            if term in document_keywords:

                score += weight

    # --------------------------------------------------------
    # VPN matching
    # --------------------------------------------------------

    if "vpn" in query_keywords:

        query_says_connected = (
            "connected"
            in query_keywords
        )

        query_mentions_applications = (
            "applications"
            in query_keywords
        )

        document_is_access_issue = (

            "company applications are not accessible"
            in document_text

            or

            "company applications cannot be accessed"
            in document_text
        )

        document_is_connection_issue = (

            "vpn is not connecting"
            in document_text

            or

            "vpn client does not connect"
            in document_text

            or

            "vpn connection fails"
            in document_text
        )

        document_is_disconnect_issue = (

            "vpn keeps disconnecting"
            in document_text

            or

            "connection drops"
            in document_text
        )

        # Strong match

        if (
            query_says_connected
            and query_mentions_applications
            and document_is_access_issue
        ):

            score += 15

        # Contradiction penalty

        if (
            query_says_connected
            and document_is_connection_issue
        ):

            score -= 8

        # Disconnect penalty

        if (
            query_says_connected
            and document_is_disconnect_issue
        ):

            score -= 3

    # --------------------------------------------------------
    # Outlook matching
    # --------------------------------------------------------

    if "outlook" in query_keywords:

        if "opening" in query_keywords:

            if (
                "outlook is not opening"
                in document_text
            ):

                score += 10

        if "emails" in query_keywords:

            if (
                "cannot send or receive emails"
                in document_text
            ):

                score += 10

        if "syncing" in query_keywords:

            if (
                "outlook is not syncing"
                in document_text
            ):

                score += 10

    # --------------------------------------------------------
    # Software matching
    # --------------------------------------------------------

    if (
        "software" in query_keywords
        or
        "installation" in query_keywords
        or
        "install" in query_keywords
    ):

        if (
            "software installation"
            in document_text

            or

            "general software installation"
            in document_text
        ):

            score += 8

    # --------------------------------------------------------
    # Password matching
    # --------------------------------------------------------

    if (
        "password" in query_keywords
        or
        "forgot" in query_keywords
        or
        "expired" in query_keywords
    ):

        if (
            "password reset guidance"
            in document_text

            or

            "forgotten password"
            in document_text

            or

            "password expired"
            in document_text
        ):

            score += 8

    return score


# ============================================================
# Retrieve
# ============================================================

def retrieve(
    query,
    top_k=DEFAULT_TOP_K,
    category=None
):

    documents = load_knowledge()

    if not documents:

        return []

    # --------------------------------------------------------
    # Normalize category
    # --------------------------------------------------------

    normalized_category = None

    if category:

        normalized_category = (
            CATEGORY_MAP.get(
                category.upper(),
                category.lower()
            )
        )

    # --------------------------------------------------------
    # Score documents
    # --------------------------------------------------------

    results = []

    for document in documents:

        document_category = (
            document.get(
                "category",
                ""
            ).lower()
        )

        # Category filtering

        if (
            normalized_category
            and
            normalized_category
            != document_category
        ):

            continue

        score = calculate_score(
            query,
            document
        )

        if score >= MIN_SCORE:

            results.append(
                {
                    "id": document.get(
                        "id"
                    ),

                    "category": document.get(
                        "category"
                    ),

                    "source": document.get(
                        "source"
                    ),

                    "content": document.get(
                        "content"
                    ),

                    "score": score,
                }
            )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    test_queries = [

        (
            "VPN is connected but I cannot "
            "access company applications",
            "VPN"
        ),

        (
            "Outlook is not opening",
            "OUTLOOK"
        ),

        (
            "How do I install approved software?",
            "SOFTWARE_INSTALLATION"
        ),

        (
            "I forgot my password",
            "PASSWORD_RESET"
        ),

    ]

    for test_query, category in test_queries:

        results = retrieve(
            query=test_query,
            top_k=3,
            category=category
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"Query: {test_query}"
        )

        print(
            f"Category: {category}"
        )

        print(
            "\nRetrieved Knowledge:\n"
        )

        for result in results:

            print(
                f"Score: {result['score']}"
            )

            print(
                f"Category: "
                f"{result['category']}"
            )

            print(
                f"Source: "
                f"{result['source']}"
            )

            print(
                f"ID: "
                f"{result['id']}"
            )

            print(
                f"Content:\n"
                f"{result['content']}"
            )

            print(
                "-" * 60
            )