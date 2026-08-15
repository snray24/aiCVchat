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
    
    def extract_candidate_id_and_designation(self, text: str, file_path: Path) -> tuple[str, str]:
        """Extract 9-digit candidate ID and designation from resume text or filename."""
        import re
        
        # Try to extract from first line of text
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Pattern: STUDENT CODE: {9-digit} {designation} ABOUT ME
        match = re.search(r'STUDENT CODE:\s*(\d{9})\s+(.+?)\s+ABOUT ME', first_line, re.IGNORECASE)
        if match:
            candidate_id = match.group(1)
            designation = match.group(2).strip()
            return candidate_id, designation
        
        # Fallback: try to extract from filename
        filename = file_path.stem
        # Pattern: {9-digit}_rest_of_filename
        match = re.search(r'(\d{9})', filename)
        if match:
            candidate_id = match.group(1)
            return candidate_id, ""
        
        # If no candidate ID found, return empty strings
        return "", ""
    
    def parse_resume_sections(self, text: str) -> dict:
        """Parse resume into the 8 required sections."""
        import re
        
        sections = {
            "about_me": "",
            "work_experience": "",
            "education": "",
            "certifications": "",
            "achievements": "",
            "skills": "",
            "interest": "",
            "personal_profile": ""
        }
        
        # Section header patterns (case-insensitive)
        section_patterns = {
            "about_me": r'ABOUT ME\s*',
            "work_experience": r'WORK EXPERIENCE\s*',
            "education": r'EDUCATION\s*',
            "certifications": r'CERTIFICATIONS\s*',
            "achievements": r'ACHIEVEMENTS\s*',
            "skills": r'SKILLS\s*',
            "interest": r'INTEREST\s*',
            "personal_profile": r'PERSONAL PROFILE\s*'
        }
        
        # Find all section positions
        section_positions = []
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                section_positions.append((match.start(), section_name))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[0])
        
        # Extract content for each section
        for i, (start_pos, section_name) in enumerate(section_positions):
            # Find end position (next section start or end of text)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract content (skip the header itself)
            section_content = text[start_pos:end_pos]
            # Remove the header line
            header_pattern = section_patterns[section_name]
            section_content = re.sub(header_pattern, '', section_content, flags=re.IGNORECASE)
            
            # Clean up the content
            section_content = section_content.strip()
            sections[section_name] = section_content
        
        return sections
    
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
