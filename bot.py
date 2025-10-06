import time
import uuid
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.chatbot import get_answer_async   
from src.logger import get_logger          
load_dotenv()

logger = get_logger(__name__)

app = FastAPI(
    title="Log Summarization & Insights Chatbot",
    version="1.0",
    description="Production-ready FastAPI service for System Engineer chatbot (LangGraph + MCP + RAG)."
)

# -------------------------------------------------------------------
# ✅ CORS (for internal dashboards or CLI clients)
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# ✅ Middleware for Request Logging
# -------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"➡️ [{request_id}] {request.method} {request.url}")

    try:
        response = await call_next(request)

    except Exception as exc:
        logger.error(f"❌ [{request_id}] Exception during request: {exc}")
        raise exc

    duration = round(time.time() - start_time, 3)
    logger.info(f"✅ [{request_id}] Completed in {duration}s (status={response.status_code})")

    return response

# -------------------------------------------------------------------
# ✅ Root Endpoint
# -------------------------------------------------------------------
@app.get("/")
def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the Log Summarization & Insights Chatbot API"}

# -------------------------------------------------------------------
# ✅ Main Chat Endpoint (async)
# -------------------------------------------------------------------
@app.get("/chat")
async def chat(query: str = Query(..., description="User query to chatbot")):
    try:
        response = await get_answer_async(query)
        logger.info(f"✅ Query processed successfully for: {query[:50]}")
        return {"query": query, "response": response}
    
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# -------------------------------------------------------------------
# ✅ Health Check Endpoint
# -------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Used by Jenkins/Cloud Run for health probes."""
    logger.info("Health check OK.")
    return {"status": "ok", "service": "chatbot-api"}

# -------------------------------------------------------------------
# ✅ Global Exception Handler 
# -------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "details": str(exc)})


