"""Email service for sending resumes via SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List
from app.core.config import settings
from app.core.logging import logger


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_from = settings.smtp_from
    
    def send_resumes(
        self,
        to_email: str,
        resume_files: List[Path],
        subject: str = "Requested Resumes"
    ) -> bool:
        """Send resumes as email attachments."""
        if not all([self.smtp_host, self.smtp_username, self.smtp_password, self.smtp_from]):
            logger.error("SMTP configuration incomplete")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_from
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Add body
            body = f"Please find the requested resumes attached.\n\nTotal resumes: {len(resume_files)}"
            msg.attach(MIMEText(body, "plain"))
            
            # Attach resumes
            for file_path in resume_files:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                with open(file_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=file_path.name)
                part["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
                msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(
            self.smtp_host and
            self.smtp_username and
            self.smtp_password and
            self.smtp_from
        )


email_service = EmailService()
