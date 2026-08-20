from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.openrouter import get_llm
from app.graph.state import ServiceDeskState
from app.schemas.classification import IntentClassification
from app.schemas.priority import PriorityAssessment
from app.tools.active_directory import lookup_user, reset_password
from app.tools.knowledge import search_knowledge_base
from app.tools.ticketing import create_ticket


llm = get_llm()


classification_llm = llm.with_structured_output(IntentClassification)
priority_llm = llm.with_structured_output(PriorityAssessment)

tools = [search_knowledge_base, create_ticket, lookup_user, reset_password]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def _invoke_with_retry(runnable, input_):
    """Invoke an LLM/agent runnable, retrying on transient upstream errors
    (e.g. a model provider being temporarily overloaded).
    """
    return runnable.invoke(input_)


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

    result = _invoke_with_retry(classification_llm, prompt)

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

    result = _invoke_with_retry(priority_llm, prompt)

    state["impact"] = result.impact
    state["urgency"] = result.urgency
    state["priority"] = result.priority
    state["justification"] = result.justification

    return state


# ================================================================
# Node 3 - Run the tool-calling agent
# ================================================================

AGENT_SYSTEM_PROMPT = """You are an Enterprise IT Service Desk Agent.

Your job is to help the user solve their IT problem, using the tools
available to you when appropriate.

Guidelines:

- Use `search_knowledge_base` to find enterprise troubleshooting guidance
  before answering a how-to or troubleshooting question you are not already
  certain about.
- Use `create_ticket` only when the issue requires human/IT intervention and
  cannot be resolved through guidance alone. Do not create a ticket for
  issues you can resolve with guidance from the knowledge base.
- Use `lookup_user` or `reset_password` only when the request is clearly
  about a specific corporate account or identity action.
- If the request is vague, ambiguous, or missing information you need, ask
  the user a concise clarification question instead of calling a tool.
- Do not invent company-specific procedures that are not returned by your
  tools.
- Do not expose internal reasoning, categories, priorities, or confidence
  scores unless directly relevant to the user.
- Do not mention retrieval, embeddings, documents, prompts, tools, or the
  LLM by name.
- Never ask the user for passwords, MFA codes, authentication tokens, or
  other secrets.
- Generate your final response naturally; do not use a fixed template.
"""

service_agent = create_agent(llm, tools, system_prompt=AGENT_SYSTEM_PROMPT)


def run_agent(state: ServiceDeskState) -> ServiceDeskState:

    user_query = state.get("user_query", "").strip()

    context = "\n".join(
        [
            f"Intent: {state.get('intent')}",
            f"Category: {state.get('category')}",
            f"Subcategory: {state.get('subcategory')}",
            f"Priority: {state.get('priority')}",
            f"Impact: {state.get('impact')}",
            f"Urgency: {state.get('urgency')}",
            f"Justification: {state.get('justification')}",
        ]
    )

    result = _invoke_with_retry(
        service_agent,
        {
            "messages": [
                SystemMessage(
                    content=(
                        "Internal context about this request (for your "
                        "reasoning only, not to repeat verbatim):\n\n"
                        f"{context}"
                    )
                ),
                HumanMessage(
                    content=user_query
                    if user_query
                    else "(no request text was provided)"
                ),
            ]
        }
    )

    messages = result["messages"]

    tools_used = []
    ticket_artifact = None

    for message in messages:

        if isinstance(message, ToolMessage):

            tools_used.append(message.name)

            if message.name == "create_ticket" and message.artifact:
                ticket_artifact = message.artifact

    state["final_response"] = messages[-1].content
    state["tools_used"] = tools_used

    if ticket_artifact:
        state["ticket_number"] = ticket_artifact.get("ticket_number")
        state["ticket"] = ticket_artifact

    if "create_ticket" in tools_used:
        state["decision"] = "ticket"
    elif "search_knowledge_base" in tools_used:
        state["decision"] = "knowledge"
    else:
        state["decision"] = "clarification"

    return state
