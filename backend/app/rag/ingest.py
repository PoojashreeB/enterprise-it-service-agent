from pathlib import Path
import json
import re


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
OUTPUT_FILE = BASE_DIR / "app" / "data" / "knowledge.json"

CHUNK_SIZE = 1200


# ============================================================
# Split Knowledge Article into Logical Sections
# ============================================================

def chunk_text(text: str):

    text = text.strip()

    if not text:
        return []

    # Normalize separators
    text = re.sub(
        r"-{20,}",
        "\n---SECTION---\n",
        text
    )

    sections = [
        section.strip()
        for section in text.split("---SECTION---")
        if section.strip()
    ]

    chunks = []

    current_chunk = ""

    for section in sections:

        # ----------------------------------------------------
        # If section is small enough, append it
        # ----------------------------------------------------

        if len(section) <= CHUNK_SIZE:

            if current_chunk:

                combined = (
                    current_chunk
                    + "\n\n"
                    + section
                )

                if len(combined) <= CHUNK_SIZE:

                    current_chunk = combined

                else:

                    chunks.append(
                        current_chunk.strip()
                    )

                    current_chunk = section

            else:

                current_chunk = section

            continue

        # ----------------------------------------------------
        # Large section
        # ----------------------------------------------------

        if current_chunk:

            chunks.append(
                current_chunk.strip()
            )

            current_chunk = ""

        # Split large section by lines
        lines = section.splitlines()

        temp = []
        temp_length = 0

        for line in lines:

            line_length = len(line) + 1

            if (
                temp
                and temp_length + line_length > CHUNK_SIZE
            ):

                chunks.append(
                    "\n".join(temp).strip()
                )

                temp = []
                temp_length = 0

            temp.append(line)

            temp_length += line_length

        if temp:

            chunks.append(
                "\n".join(temp).strip()
            )

    if current_chunk:

        chunks.append(
            current_chunk.strip()
        )

    return chunks


# ============================================================
# Ingest Knowledge
# ============================================================

def ingest_knowledge():

    if not KNOWLEDGE_DIR.exists():

        raise FileNotFoundError(
            f"Knowledge directory not found: "
            f"{KNOWLEDGE_DIR}"
        )

    txt_files = list(
        KNOWLEDGE_DIR.rglob("*.txt")
    )

    if not txt_files:

        raise FileNotFoundError(
            f"No knowledge files found in: "
            f"{KNOWLEDGE_DIR}"
        )

    records = []

    for file_path in txt_files:

        text = file_path.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(text)

        category = file_path.parent.name

        for index, chunk in enumerate(chunks):

            records.append(
                {
                    "id": f"{category}_{index}",
                    "category": category,
                    "source": file_path.name,
                    "content": chunk,
                }
            )

    # --------------------------------------------------------
    # Ensure output directory exists
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Write JSON
    # --------------------------------------------------------

    OUTPUT_FILE.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        f"Successfully ingested "
        f"{len(records)} knowledge chunks."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    ingest_knowledge()