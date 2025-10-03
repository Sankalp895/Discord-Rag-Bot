from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from PyPDF2 import PdfReader
from pydantic import BaseModel #for to handle structure of query
import logging
from deepseek import ask_deepseek
from embeddings import EmbeddingManager
import json
from fastapi.responses import JSONResponse
from logging.handlers import RotatingFileHandler
from prometheus_client import Counter, Histogram, start_http_server
import docx




logger = logging.getLogger("rag_backend")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler() #path of logs
ch.setLevel(logging.INFO)

fh = RotatingFileHandler("rag_backend.log", maxBytes=5*1024*1024, backupCount=3)
fh.setLevel(logging.INFO) 

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(name)s] [%(module)s] %(message)s"
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
#how the logs would be displayed, #astime == timestamp, levelname:- at what log, message
logger.addHandler(ch)
logger.addHandler(fh)
# Initialize FastAPI
start_http_server(8001) #metrics available at local host 8001
# Track total requests to the RAG query endpoint
REQUEST_COUNT = Counter("rag_requests_total", "Total number of RAG queries")
REQUEST_LATENCY = Histogram("rag_request_latency_seconds", "Time taken for RAG queries")
FEEDBACK_COUNT = Counter("feedback_submissions_total", "Number of feedback submissions")
DOC_INGEST_COUNT = Counter("documents_ingested_total", "Number of documents ingested")

app = FastAPI(title="RAG Backend API")
#handle incoming requests like a recptionist
# Root endpoint (optional, for testing)
@app.get("/")
async def root():
    return {"message": "RAG Backend is running!"}

# Initialize Embedding Manager
embedding_manager = EmbeddingManager()

# BaseModel here is to validate input data
class QueryRequest(BaseModel):
    query: str #must be a string

class FeedbackRequest(BaseModel):
    query: str
    rag_response: str
    rating: int  # e.g., 1-5
    comment: str = None  # optional user comment

# Feedback storage (simple in-memory list for now)
feedback_store = []

class IngestRequest(BaseModel):
    title: str
    content: str
    metadata: dict | None = None

@app.post("/api/ingest-file")
async def ingest_file(file: UploadFile = File(...), title: str = None):
    DOC_INGEST_COUNT.inc()
    try:
        content = ""
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        elif file.filename.endswith(".docx"):
            doc = docx.Document(file.file)
            for para in doc.paragraphs:
                content += para.text + "\n"
        else:
            return {"error": "Unsupported file type. Use PDF or DOCX."}

        # Use filename if no title provided
        doc_title = title or file.filename
        embedding_manager.add_document(content, metadata={"title": doc_title})

        logger.info(f"File '{doc_title}' ingested successfully")
        return {"message": f"File '{doc_title}' ingested successfully!"}

    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/feedback")
async def feedback(request: FeedbackRequest):
    FEEDBACK_COUNT.inc()
    try:
        feedback_data = {
            "query": request.query,
            "rag_response": request.rag_response,
            "rating": request.rating,
            "comment": request.comment,
        }
        feedback_store.append(feedback_data)

        # Save persistently to file
        with open("feedback.json", "w", encoding="utf-8") as f:
            json.dump(feedback_store, f, ensure_ascii=False, indent=2)

        logger.info(f"Feedback received: {feedback_data}")
        return {"message": "Feedback received successfully!"}

    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/feedback")
async def get_feedback():
    try:
        return JSONResponse(content=feedback_store)
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))    

@app.post("/api/rag-query") #we define post endoint here to interact with the api
async def rag_query(request: QueryRequest):#asynchronous connection
   REQUEST_COUNT.inc()
   with REQUEST_LATENCY.time():
     query_text = request.query.strip()
     logger.info(f"Received query: {query_text}")

     try:
        # Embed query
        query_vector = embedding_manager.embed_query(query_text)
        logger.info("Query embedding generated")

        # Search FAISS
        top_answers = embedding_manager.search_faq(query_vector)
        logger.info(f"Top FAQ answers: {top_answers}")

        # DeepSeek response
        context = " ".join(top_answers)
        deepseek_response = ask_deepseek(query_text, context)
        logger.info("DeepSeek response generated")

        return {"query": query_text, "answers": top_answers, "rag_response": deepseek_response}

     except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
