from langchain_core.tools import tool

from app.rag.retriever import retrieve


@tool
def search_knowledge_base(query: str) -> str:
    """Search the enterprise IT knowledge base for troubleshooting guidance
    relevant to the user's issue. Call this before answering a how-to or
    troubleshooting question you are not already certain about.
    """
    documents = retrieve(query=query, top_k=5)

    if not documents:
        return "No relevant enterprise knowledge was found."

    parts = [
        f"Source: {document.get('source')}\nKnowledge:\n{document.get('content')}"
        for document in documents
    ]

    return "\n\n".join(parts)
