from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.utilities import SerpAPIWrapper
from typing import TypedDict, List, Optional
import os
from dotenv import load_dotenv

from langfuse import Langfuse
from langfuse.callback import CallbackHandler

load_dotenv()

try:
    langfuse = Langfuse()
    print("Langfuse initialized")
except Exception as e:
    print(f"Langfuse not connected: {e}")
    langfuse = None


class AgentState(TypedDict):
    messages: List
    response: str
    search_results: Optional[str]
    needs_search: bool


print("DEBUG GROQ_API_KEY =", os.getenv("GROQ_API_KEY"))

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
)

search = SerpAPIWrapper(
    serpapi_api_key=os.getenv("SERPAPI_API_KEY")
)


def router_node(state: AgentState) -> AgentState:
    print("\n[Router] Deciding if search is needed...")

    last_message = state["messages"][-1].content
    handler = CallbackHandler()

    decision = llm.invoke(
        [
            SystemMessage(
                content="""You decide if a question needs a web search or not.
Reply with ONLY 'search' or 'chat'. Nothing else.
- Use 'search' for: current events, news, prices, weather, recent facts
- Use 'chat' for: casual talk, general knowledge, opinions, advice"""
            ),
            HumanMessage(content=last_message),
        ],
        config={"callbacks": [handler]},
    )

    state["needs_search"] = "search" in decision.content.lower()
    print(f"[Router] Decision: {'search' if state['needs_search'] else 'chat'}")
    return state


def search_node(state: AgentState) -> AgentState:
    print("\n[Search Agent] Fetching from web...")

    query = state["messages"][-1].content

    try:
        results = search.run(query)
        state["search_results"] = results
        print(f"[Search Agent] Got results: {results[:200]}...")
    except Exception as e:
        state["search_results"] = f"Search failed: {e}"
        print(f"[Search Agent] Error: {e}")

    return state


def chat_node(state: AgentState) -> AgentState:
    print("\n[Chat Node] Thinking...")

    search_context = ""
    if state.get("search_results"):
        search_context = (
            f"\n\nWeb search results:\n{state['search_results']}\n\nUse this to answer."
        )

    messages = [
        SystemMessage(
            content=f"You are a chill, friendly assistant. "
                    f"Keep replies short and casual.{search_context}"
        ),
        *state["messages"],
    ]

    handler = CallbackHandler()

    response = llm.invoke(
        messages,
        config={"callbacks": [handler]},
    )

    state["messages"].append(AIMessage(content=response.content))
    state["response"] = response.content
    state["search_results"] = None

    print(f"[Chat Node] Done: {response.content}")
    return state


def route_decision(state: AgentState) -> str:
    return "search" if state.get("needs_search") else "chat"


graph = StateGraph(AgentState)

graph.add_node("router", router_node)
graph.add_node("search", search_node)
graph.add_node("chat", chat_node)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    route_decision,
    {"search": "search", "chat": "chat"},
)

graph.add_edge("search", "chat")
graph.add_edge("chat", END)

app = graph.compile()


def run_agent(question: str) -> str:
    result = app.invoke(
        {
            "messages": [HumanMessage(content=question)],
            "response": "",
            "search_results": None,
            "needs_search": False,
        }
    )
    return result["response"]


def ask_questions_from_terminal():
    print("\nAsk your questions below.")
    print("Type one question at a time.")
    print("Press ENTER on an empty line to exit.\n")

    while True:
        question = input("> ").strip()
        if not question:
            print("Exiting.")
            break

        answer = run_agent(question)

        print(f"\nAssistant:\n{answer}\n")
        print("-" * 60)


if __name__ == "__main__":
    ask_questions_from_terminal()