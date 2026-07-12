"""Resume parsing service for PDF and DOCX files."""
import hashlib
from pathlib import Path
from typing import Dict, Any
import pypdf
import docx
from app.core.logging import logger


class ResumeParser:
    """Parser for resume files (PDF and DOCX)."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF extraction error for {file_path}: {e}")
        return self._normalize_text(text)
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX extraction error for {file_path}: {e}")
        return self._normalize_text(text)
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from file based on extension."""
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace in text."""
        import re
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)
        # Remove excessive newlines
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        return text.strip()
    
    def parse_deterministic_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata using deterministic parsing (no LLM)."""
        import re
        
        # Simple email extraction
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        
        # Simple phone extraction
        phones = re.findall(r"\+?[\d\s\-\(\)]{10,}", text)
        
        # Look for common patterns
        metadata = {
            "emails": emails,
            "phones": phones,
            "text_length": len(text)
        }
        
        return metadata


resume_parser = ResumeParser()
