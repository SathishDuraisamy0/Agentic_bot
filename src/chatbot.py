import os
import csv
import time
import re
import asyncio
import numpy as np
from datetime import datetime

from groq import Groq
from sklearn.metrics.pairwise import cosine_similarity
from langgraph.graph import StateGraph
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from src.MCP_tools import tavily_search_summary, search_github_code, get_weather
from src.logger import get_logger
from src.custom_exception import CustomException

# --------------------------------------------------------------------------
# Logger setup
# --------------------------------------------------------------------------
logger = get_logger(__name__)

# --------------------------------------------------------------------------
# Paths and constants
# --------------------------------------------------------------------------
VECTOR_DB_DIR = os.path.join("artifacts", "VECTOR_DB")
FEEDBACK_PATH = os.path.join("artifacts", "feedback_log.csv")
os.makedirs("artifacts", exist_ok=True)

INTENT_CONFIDENCE_THRESHOLD = 0.5
TOP_K_RETRIEVAL = 3
GROQ_MODEL = "llama-3.3-70b-versatile"

# --------------------------------------------------------------------------
# Embeddings and retriever
# --------------------------------------------------------------------------
try:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(VECTOR_DB_DIR, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K_RETRIEVAL})
    logger.info("✅ FAISS retriever loaded successfully.")
except Exception as e:
    logger.error(f"❌ Failed to load FAISS retriever: {e}")
    retriever = None

# --------------------------------------------------------------------------
# Groq client (optional)
# --------------------------------------------------------------------------
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("✅ Groq client initialized.")
except Exception as e:
    logger.error(f"❌ Groq init failed: {e}")
    client = None

# --------------------------------------------------------------------------
# Latency helper
# --------------------------------------------------------------------------
async def measure_latency(coro, label: str, *args, **kwargs):
    start = time.perf_counter()
    result = await coro(*args, **kwargs)
    ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"⏱️ {label} completed in {ms} ms")
    return result
# --------------------------------------------------------------------------
# 🚀 LLM-Only Semantic Router 
# --------------------------------------------------------------------------
class SemanticRouter:
    def __init__(self, _embeddings, _retriever):
        self.embeddings = _embeddings
        self.retriever = _retriever
        logger.info("✅ Router initialized: LLM-only intent classification mode")

    # ----------------------------------------------------------------------
    # 🧠 Step 1: LLM decides which tool to use
    # ----------------------------------------------------------------------
    async def classify_intent_with_llm(self, query: str) -> str:
        """Always classify using LLM — no embedding scoring."""
        if not client:
            logger.warning("⚠️ Groq client missing; fallback to RAG.")
            return "RAG"

        try:
            prompt = (
                "You are an intelligent routing assistant.\n"
                "Classify the user's query into exactly ONE category from this list:\n"
                "[Weather, Tavily, GitHub, RAG].\n\n"
                "Rules:\n"
                "- Use 'Weather' for temperature, rain, or city climate queries.\n"
                "- Use 'Tavily' for general knowledge or web information.\n"
                "- Use 'GitHub' for coding, repositories, or script examples.\n"
                "- Use 'RAG' for internal policy, logs, or documentation queries.\n\n"
                f"User Query: {query}\n\n"
                "Return only the category name (no explanation)."
            )

            def _call_llm():
                return client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=20,
                )

            resp = await asyncio.to_thread(_call_llm)
            answer = resp.choices[0].message.content.strip()
            logger.info(f"🧩 LLM classified → {answer}")

            if answer not in ["Weather", "Tavily", "GitHub", "RAG"]:
                return "RAG"
            return answer

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return "RAG"

    # ----------------------------------------------------------------------
    # 🧭 Step 2: Route query → correct MCP tool → optional refinement
    # ----------------------------------------------------------------------
    async def route(self, state: dict) -> dict:
        """Route query using only LLM classifier."""
        try:
            query = state["query"]

            # Use LLM for routing
            best_intent = await self.classify_intent_with_llm(query)
            logger.info(f"🧭 Routed → {best_intent}")

            raw_result = None

            # Execute the corresponding tool
            if best_intent == "Weather":
                raw_result = get_weather(12.97, 77.59)
                state["source"] = "Weather"

            elif best_intent == "Tavily":
                raw_result = tavily_search_summary(query)
                state["source"] = "Tavily"

            elif best_intent == "GitHub":
                raw_result = search_github_code(query)
                state["source"] = "GitHub"

            elif best_intent == "RAG":
                if self.retriever:
                    docs = await asyncio.to_thread(self.retriever.invoke, query)
                    context = "\n".join([d.page_content for d in docs])
                    state["context"] = context
                    state["source"] = "RAG"
                else:
                    state["result"] = "Retriever not available."
                    state["source"] = "Error"
                return state
            else:
                state["result"] = "No valid route found."
                state["source"] = "Unknown"
                return state

            # Optional LLM refinement (clarify response)
            if client and raw_result and state["source"] in ["Weather", "Tavily", "GitHub"]:
                try:
                    prompt = (
                        "You are a helpful assistant. Improve clarity and tone of the result.\n\n"
                        f"User Query: {query}\n"
                        f"Tool Output: {raw_result}\n\n"
                        "Refined Answer:"
                    )

                    def _call_refine():
                        return client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0,
                            max_tokens=250,
                        )

                    resp = await asyncio.to_thread(_call_refine)
                    state["result"] = resp.choices[0].message.content.strip()
                    logger.info(f"✨ LLM refinement applied for {state['source']}")
                except Exception as e:
                    logger.error(f"LLM refinement failed: {e}")
                    state["result"] = raw_result
            else:
                state["result"] = raw_result

            return state

        except Exception as e:
            logger.error(f"Router error: {e}")
            state["result"] = f"Router error: {e}"
            state["source"] = "Router Error"
            return state

router = SemanticRouter(embeddings, retriever)

# --------------------------------------------------------------------------
# LangGraph Nodes
# --------------------------------------------------------------------------
async def router_node(state):
    return await measure_latency(router.route, "Router", state)

async def rag_llm_node(state):
    """RAG → LLM generation."""
    try:
        if state.get("source") != "RAG":
            return state

        if not client:
            state["result"] = "LLM not available."
            return state

        context = state.get("context", "")
        prompt = (
            "You are an AI assistant for system engineers.\n"
            "Use the context below to answer accurately.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {state['query']}\n"
            "Answer:"
        )

        def _call_groq():
            return client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=350,
            )

        resp = await measure_latency(asyncio.to_thread, "Groq LLM", _call_groq)
        state["result"] = resp.choices[0].message.content.strip()
        return state
    except Exception as e:
        logger.error(f"❌ RAG LLM error: {e}")
        state["result"] = f"LLM error: {e}"
        return state


async def feedback_node(state):
    """Collect feedback."""
    try:
        logger.info(f"📘 Source: {state.get('source')}")
        print(f"\nAssistant: {state.get('result')}\n")
        rating = input("Rate the answer (1-5): ").strip()
        comment = input("Optional comment: ").strip()

        is_new = not os.path.exists(FEEDBACK_PATH)
        with open(FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(["timestamp", "source", "rating", "comment", "query"])
            writer.writerow([
                datetime.now().isoformat(),
                state.get("source"),
                rating,
                comment,
                state.get("query")
            ])

        logger.info("🗳️ Feedback saved.")
        return state
    except Exception as e:
        logger.error(f"❌ Feedback error: {e}")
        return state

# --------------------------------------------------------------------------
# LangGraph Workflow
# --------------------------------------------------------------------------
workflow = StateGraph(dict)
workflow.add_node("Router", router_node)
workflow.add_node("RAG_LLM", rag_llm_node)
workflow.add_node("Feedback", feedback_node)

workflow.set_entry_point("Router")

workflow.add_conditional_edges(
    "Router",
    lambda state: "RAG_LLM" if state.get("source") == "RAG" else "Feedback",
    path_map={"RAG_LLM": "RAG_LLM", "Feedback": "Feedback"},
)
workflow.add_edge("RAG_LLM", "Feedback")

graph = workflow.compile()

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
async def get_answer_async(query: str) -> str:
    """Run one chatbot cycle for a given query (used in FastAPI or other apps)."""
    try:
        state = {"query": query}
        result_state = await graph.ainvoke(state)
        return result_state.get("result", "No response generated.")
    except Exception as e:
        logger.error(f"❌ get_answer_async error: {e}")
        return f"Error: {e}"

def get_answer(query: str) -> str:
    """Synchronous wrapper for get_answer_async."""
    return asyncio.run(get_answer_async(query))