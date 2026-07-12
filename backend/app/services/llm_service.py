"""LLM service for chat completion and answer generation."""
from typing import List, Dict
from app.services.ollama_client import ollama_client
from app.core.logging import logger


class LLMService:
    """Service for LLM-based text generation."""
    
    def __init__(self):
        self.client = ollama_client
        self.system_prompt = """You are a resume search assistant. Use only the provided resume context to answer questions.

Rules:
- Never fabricate names, employers, experience, degrees, skills, or years
- If information is not in the retrieved context, say it is not available in the indexed resumes
- Prefer bullet summaries for clarity
- Keep answers under 180 words unless user explicitly asks for more
- When listing candidates, include why they match
- Never mention internal retrieval mechanics
- Be concise and accurate"""
    
    async def generate_answer(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]] | None = None
    ) -> str:
        """Generate answer based on query and retrieved context."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        # Note: History is currently not used to avoid context confusion
        # Each query is answered independently based on current retrieval results
        # If conversation history is needed, it should be integrated with context retrieval
        
        try:
            answer = await self.client.chat(messages)
            return answer.strip()
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return "I apologize, but I encountered an error generating a response. Please try again."
    
    async def extract_metadata(self, resume_text: str) -> Dict[str, any]:
        """Extract structured metadata from resume text using LLM."""
        prompt = f"""Extract the following information from this resume. Return ONLY a JSON object with these exact keys:
- full_name
- current_title
- total_years_experience (as number)
- summary (2-3 sentences)
- skills (comma-separated list)
- education (comma-separated list)
- certifications (comma-separated list)
- last_company
- location

If a field cannot be found, use null.

Resume text:
{resume_text[:3000]}"""
        
        messages = [
            {"role": "system", "content": "You are a resume parser. Return only valid JSON, no other text."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.client.chat(messages)
            # Simple JSON extraction - in production use more robust parsing
            import json
            # Try to find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return {}


llm_service = LLMService()
