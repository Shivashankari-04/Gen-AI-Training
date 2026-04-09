import os
import faiss
import numpy as np
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

load_dotenv()

# We enforce exactly matching structured attributes for the LLM
class MCQ(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: str

class QuizResponse(BaseModel):
    questions: List[MCQ]

class RAGAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        self.generator_model = "gpt-4o-mini"
        self.dimension = 1536 # Dimensionality of text-embedding-3-small
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.chunk_size = 500

    async def _get_embedding(self, text: str) -> np.ndarray:
        response = await self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return np.array(response.data[0].embedding, dtype="float32")
    
    def _chunk_text(self, text: str) -> List[str]:
        # Simple character-based chunking for token optimization without overlap
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0
        for word in words:
            if current_len + len(word) > self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_len = len(word)
            else:
                current_chunk.append(word)
                current_len += len(word) + 1
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    async def ingest_document(self, text: str):
        chunks = self._chunk_text(text)
        if not chunks:
            return
            
        embeddings = []
        for chunk in chunks:
            emb = await self._get_embedding(chunk)
            embeddings.append(emb)
        
        # Add to FAISS index
        emb_matrix = np.vstack(embeddings)
        self.index.add(emb_matrix)
        self.documents.extend(chunks)
        
        return {"status": "success", "chunks_added": len(chunks)}

    async def retrieve(self, query: str, top_k: int = 2) -> List[str]:
        """Limits context size by aggressively fetching only top_k results."""
        if self.index.ntotal == 0:
            return []
            
        query_emb = await self._get_embedding(query)
        query_emb = np.expand_dims(query_emb, axis=0)
        
        distances, indices = self.index.search(query_emb, top_k)
        retrieved_docs = []
        for idx in indices[0]:
            if idx < len(self.documents) and idx >= 0:
                retrieved_docs.append(self.documents[idx])
        return retrieved_docs

    async def generate_quiz(self, topic: str, count: int = 3) -> dict:
        """Retrieves specific chunks and calls LLM to generate MCQ strictly in JSON."""
        # Retrieve small highly relevant chunk context
        retrieved_contexts = await self.retrieve(topic)
        context_text = "\n".join(retrieved_contexts) if retrieved_contexts else "General knowledge context."

        system_prompt = (
            "You are an expert AI tutor. Generate exactly {count} multiple-choice questions "
            "based on the provided context about '{topic}'. "
            "Ensure the questions and answers strictly follow the schema provided. "
            "Do not output markdown code blocks. Keep token count low."
        ).format(count=count, topic=topic)

        user_content = f"Context Context:\n{context_text}"

        response = await self.client.beta.chat.completions.parse(
            model=self.generator_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=QuizResponse,
            max_tokens=800 # Token constraint
        )

        # The JSON returned is already validated into the Pydantic shape
        # Returning it as a dict
        return response.choices[0].message.parsed.model_dump()

rag_agent = RAGAgent()
