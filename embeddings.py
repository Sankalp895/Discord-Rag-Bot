import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging

class EmbeddingManager:
    def __init__(self, faq_file="faqs.json", model_name="all-MiniLM-L6-v2"):
        with open(faq_file, 'r') as f:
            self.faq = json.load(f)

        self.questions = [item["question"] for item in self.faq]
        self.answers = [item["answer"] for item in self.faq]


        self.embedder = SentenceTransformer(model_name)

        self.question_embeddings = self.embedder.encode(self.questions, convert_to_numpy=True)

        #FAISS index
        dim = self.question_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.question_embeddings)

        logging.info(f"FAISS index built with {len(self.questions)} questions")

    def embed_query(self, query: str):
        return np.array([self.embedder.encode(query)])

    def search_faq(self, query_vector, k=3):
        distances, indices = self.index.search(query_vector, k)
        results = [self.answers[i] for i in indices[0]]
        return results
    
    def add_document(self, content: str, metadata: dict = None):
     try:
        
        new_embedding = self.embedder.encode([content], convert_to_numpy=True)
        if new_embedding.ndim == 1:
            new_embedding = new_embedding.reshape(1, -1)
        self.index.add(new_embedding)

       
        doc_question = (metadata.get("title") if metadata else None) or (content[:50] + "...")

 
        doc_entry = {
            "question": doc_question,
            "answer": content,
            "metadata": metadata or {}
        }

        # Update memory
        self.faq.append(doc_entry)
        self.questions.append(doc_entry["question"])
        self.answers.append(doc_entry["answer"])

        # Persist to file
        with open("faqs.json", "w", encoding="utf-8") as f:
            json.dump(self.faq, f, ensure_ascii=False, indent=2)

        logging.info(f"Document added: {doc_entry['question']}")
        return True

     except Exception as e:
        logging.error(f"Error in add_document: {e}")
        raise


    
