"""Text chunking service for resume segmentation."""
from typing import List
from app.core.config import settings
from app.core.logging import logger


class ChunkingService:
    """Service for chunking text into smaller segments."""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Try to break at word boundary
            if end < text_length:
                # Find last space before end
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def chunk_with_metadata(self, text: str, metadata: dict | None = None) -> List[dict]:
        """Chunk text and attach metadata to each chunk."""
        chunks = self.chunk_text(text)
        chunk_objects = []
        
        for idx, chunk in enumerate(chunks):
            chunk_obj = {
                "chunk_index": idx,
                "chunk_text": chunk,
                "metadata": metadata or {}
            }
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def chunk_sections(self, sections: dict, candidate_id: str) -> List[dict]:
        """Chunk each section separately and attach section_type metadata."""
        from app.models.resume_chunk import SectionType
        
        section_mapping = {
            "about_me": SectionType.ABOUT_ME,
            "work_experience": SectionType.WORK_EXPERIENCE,
            "education": SectionType.EDUCATION,
            "certifications": SectionType.CERTIFICATIONS,
            "achievements": SectionType.ACHIEVEMENTS,
            "skills": SectionType.SKILLS,
            "interest": SectionType.INTEREST,
            "personal_profile": SectionType.PERSONAL_PROFILE
        }
        
        all_chunks = []
        global_chunk_index = 0
        
        for section_name, section_content in sections.items():
            if not section_content or not section_content.strip():
                continue
            
            section_type = section_mapping.get(section_name)
            if not section_type:
                continue
            
            chunks = self.chunk_text(section_content)
            
            for chunk in chunks:
                chunk_obj = {
                    "chunk_index": global_chunk_index,
                    "chunk_text": chunk,
                    "section_type": section_type.value,
                    "candidate_id": candidate_id,
                    "metadata": {
                        "section_type": section_type.value,
                        "candidate_id": candidate_id
                    }
                }
                all_chunks.append(chunk_obj)
                global_chunk_index += 1
        
        return all_chunks


chunking_service = ChunkingService()
