from app.core.openrouter import get_llm
from app.graph.state import ServiceDeskState
from app.rag.retriever import retrieve
from app.schemas.classification import IntentClassification
from app.schemas.priority import PriorityAssessment
from app.schemas.decision import Decision
from app.services.ticket_service import create_ticket as create_ticket_record


llm = get_llm()


classification_llm = llm.with_structured_output(IntentClassification)
priority_llm = llm.with_structured_output(PriorityAssessment)
decision_llm = llm.with_structured_output(Decision)


# ================================================================
# Node 1 - Classify the request
# ================================================================

def classify_request(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    prompt = f"""
You are an Enterprise IT Service Desk Agent.

Analyze the user's request below and classify it.

Determine, purely from the content of the request itself:

- The underlying intent of the request.
- The most fitting category for this type of IT issue.
- The most fitting subcategory within that category.
- A confidence score between 0 and 1 reflecting how certain
  you are about this classification given the information
  provided.

Do not restrict yourself to any predefined or fixed list of
categories. Invent whatever category and subcategory best
describe this specific request. If the request is vague,
incomplete, or ambiguous, reflect that honestly with a lower
confidence score rather than guessing.

User request:

{user_query if user_query else "(no request text was provided)"}
"""

    result = classification_llm.invoke(prompt)

    state["intent"] = result.intent
    state["category"] = result.category
    state["subcategory"] = result.subcategory
    state["confidence"] = result.confidence

    return state


# ================================================================
# Node 2 - Assess priority
# ================================================================

def assess_priority(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    prompt = f"""
You are an Enterprise IT Service Desk Agent responsible for
triaging incoming requests.

Based on the request and its classification below, assess the
business impact, urgency, and overall priority.

User request:

{user_query if user_query else "(no request text was provided)"}

Classification:

Intent: {state.get("intent")}
Category: {state.get("category")}
Subcategory: {state.get("subcategory")}
Confidence: {state.get("confidence")}

Determine, using your own judgment of this specific situation
(do not apply a fixed rule table):

- The business impact of this issue.
- The urgency with which it needs to be addressed.
- An overall priority level, expressed as P1 (highest) through
  P5 (lowest), reasoned from the impact and urgency you
  identified.
- A short justification explaining why you assigned that
  priority.
"""

    result = priority_llm.invoke(prompt)

    state["impact"] = result.impact
    state["urgency"] = result.urgency
    state["priority"] = result.priority
    state["justification"] = result.justification

    return state


# ================================================================
# Node 3 - Decide the next step
# ================================================================

def decide_next_step(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    prompt = f"""
You are an Enterprise IT Service Desk Agent deciding how to
handle an incoming request.

User request:

{user_query if user_query else "(no request text was provided)"}

Classification:

Intent: {state.get("intent")}
Category: {state.get("category")}
Subcategory: {state.get("subcategory")}
Confidence: {state.get("confidence")}

Priority assessment:

Impact: {state.get("impact")}
Urgency: {state.get("urgency")}
Priority: {state.get("priority")}
Justification: {state.get("justification")}

Decide the single best next step for handling this specific
request, choosing from:

- "knowledge": the request can likely be resolved with IT
  troubleshooting knowledge/guidance.
- "clarification": the request is unclear, ambiguous, or is
  missing information needed to help the user.
- "ticket": the request requires action or intervention by IT
  staff that cannot be resolved through guidance alone.

Base this decision entirely on your own reasoning about this
specific request, its classification, and its priority. Explain
your reasoning briefly.
"""

    result = decision_llm.invoke(prompt)

    state["decision"] = result.decision

    return state


# ================================================================
# Node 4 - Retrieve enterprise knowledge
# ================================================================

def retrieve_knowledge(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    documents = retrieve(
        query=user_query,
        top_k=5,
    )

    state["retrieved_documents"] = documents

    if documents:

        knowledge_parts = []

        for document in documents:

            knowledge_parts.append(
                f"""
Source:
{document.get("source")}

Knowledge:
{document.get("content")}
"""
            )

        state["knowledge"] = "\n".join(knowledge_parts)

    else:

        state["knowledge"] = (
            "No relevant enterprise knowledge was found."
        )

    return state


# ================================================================
# Node 5 - Ask a clarification question
# ================================================================

def ask_clarification(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    prompt = f"""
You are an Enterprise IT Service Desk Agent.

The request below does not yet contain enough information to
help the user effectively.

User request:

{user_query if user_query else "(no request text was provided)"}

Classification so far:

Intent: {state.get("intent")}
Category: {state.get("category")}
Subcategory: {state.get("subcategory")}
Confidence: {state.get("confidence")}

Write a single, concise clarification question that asks for
exactly the information you need to help this specific user.
Tailor it to what is actually missing from their request rather
than asking a generic question.
"""

    response = llm.invoke(prompt)

    state["clarification_question"] = response.content

    return state


# ================================================================
# Node 6 - Create a ticket
# ================================================================

def create_ticket(state: ServiceDeskState) -> ServiceDeskState:

    ticket = create_ticket_record(
        category=state.get("category", ""),
        subcategory=state.get("subcategory", ""),
        priority=state.get("priority", ""),
        impact=state.get("impact", ""),
        urgency=state.get("urgency", ""),
        justification=state.get("justification", ""),
        user_query=state.get("user_query", ""),
    )

    state["ticket_number"] = ticket["ticket_number"]

    return state


# ================================================================
# Node 7 - Generate the final response
# ================================================================

def generate_response(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    decision = state.get("decision")

    context_parts = [
        f"Intent: {state.get('intent')}",
        f"Category: {state.get('category')}",
        f"Subcategory: {state.get('subcategory')}",
        f"Priority: {state.get('priority')}",
    ]

    if decision == "knowledge":
        context_parts.append(
            f"Enterprise knowledge:\n{state.get('knowledge')}"
        )

    if decision == "clarification":
        context_parts.append(
            "Clarification question to ask the user:\n"
            f"{state.get('clarification_question')}"
        )

    if decision == "ticket":
        context_parts.append(
            f"Ticket created: {state.get('ticket_number')}"
        )
        context_parts.append(
            f"Justification: {state.get('justification')}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an Enterprise IT Service Desk Agent.

Your job is to help the user solve their IT problem.

User request:

{user_query if user_query else "(no request text was provided)"}

Internal context (for you to reason with, not to repeat
verbatim):

{context}

Instructions:

- Understand the user's actual problem.
- If enterprise knowledge is provided, prefer it and give
  practical troubleshooting steps based on it.
- If a clarification question is provided, ask the user that
  question in a natural, concise way.
- If a ticket has been created, let the user know a ticket was
  raised, share the ticket number, and explain what happens
  next.
- Do not invent company-specific procedures that were not given
  to you.
- Do not expose internal reasoning, categories, priorities, or
  confidence scores unless directly relevant to the user.
- Do not mention RAG, retrieval, embeddings, documents,
  prompts, or the LLM.
- Do not use a predefined response template. Generate the
  response naturally based on this specific situation.
- Never ask the user for passwords, MFA codes, authentication
  tokens, or other secrets.

Generate the final response for the user.
"""

    response = llm.invoke(prompt)

    state["final_response"] = response.content

    return state
