from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.utilities import SerpAPIWrapper
from typing import TypedDict, List, Optional
import os
import requests
from bs4 import BeautifulSoup
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
    temperature=0.7
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
        raw = search.results(query)
        organic = raw.get("organic_results", [])
        state["search_results"] = organic
        print(f"[Search Agent] Found {len(organic)} results")
    except Exception as e:
        state["search_results"] = []
        print(f"[Search Agent] Error: {e}")

    return state


def fetch_article_node(state: AgentState) -> AgentState:
    print("\n[Fetch Agent] Reading full articles...")

    results = state.get("search_results", [])
    articles_text = ""

    for item in results[:2]:
        url = item.get("link")
        if not url:
            continue

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs[:10])

            articles_text += f"\n\nSource: {url}\n{text.strip()}\n"
            print(f"[Fetch Agent] Fetched: {url}")

        except Exception as e:
            print(f"[Fetch Agent] Failed {url}: {e}")

    state["search_results"] = articles_text or "No article content found."
    return state


def chat_node(state: AgentState) -> AgentState:
    print("\n[Chat Node] Thinking...")

    search_context = ""
    if state.get("search_results"):
        search_context = (
            f"\n\nHere is content fetched from the web:\n"
            f"{state['search_results']}\n\nUse this to give an accurate answer."
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
graph.add_node("fetch", fetch_article_node)
graph.add_node("chat", chat_node)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    route_decision,
    {"search": "search", "chat": "chat"},
)

graph.add_edge("search", "fetch")
graph.add_edge("fetch", "chat")
graph.add_edge("chat", END)

app = graph.compile()


def ask_questions_from_terminal():
    print("\nAsk your questions below.")
    print("Type one question per line.")
    print("Press ENTER on an empty line to exit.\n")

    while True:
        question = input("> ").strip()
        if not question:
            print("Exiting.")
            break

        result = app.invoke(
            {
                "messages": [HumanMessage(content=question)],
                "response": "",
                "search_results": None,
                "needs_search": False,
            }
        )

        print(f"\nAssistant:\n{result['response']}\n")
        print("-" * 60)


if __name__ == "__main__":
    ask_questions_from_terminal()