from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import json

load_dotenv()

class SupabaseService:
    """Service for interacting with Supabase database"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = "ai_assessments"  # Your Supabase table name
    
    def get_pending_assessments(self):
        """
        Fetch assessments that need processing
        (analysis_completed=False OR pdf_generated=False OR email_sent=False)
        """
        try:
            response = self.client.table(self.table_name).select("*").or_(
                "analysis_completed.eq.false,pdf_generated.eq.false,email_sent.eq.false"
            ).order("created_at", desc=True).execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching pending assessments: {e}")
            return []
    
    def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict[Any, Any]]:
        """Fetch a specific assessment by ID"""
        try:
            response = self.client.table(self.table_name).select("*").eq(
                "id", assessment_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching assessment {assessment_id}: {e}")
            return None
    
    def get_latest_assessment(self) -> Optional[Dict[Any, Any]]:
        """Fetch the most recent assessment"""
        try:
            response = self.client.table(self.table_name).select("*").order(
                "created_at", desc=True
            ).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching latest assessment: {e}")
            return None
    
    def update_analysis_status(self, assessment_id: str, 
                              calculated_score: int = None,
                              score_level: str = None,
                              chatgpt_analysis: dict = None):
        """Update assessment with ChatGPT analysis results"""
        try:
            update_data = {
                "analysis_completed": True
            }
            
            if calculated_score is not None:
                update_data["calculated_score"] = calculated_score
            
            if score_level:
                update_data["score_level"] = score_level
            
            if chatgpt_analysis:
                update_data["chatgpt_analysis"] = chatgpt_analysis
            
            response = self.client.table(self.table_name).update(
                update_data
            ).eq("id", assessment_id).execute()
            
            return True
        except Exception as e:
            print(f"Error updating analysis status: {e}")
            return False
    
    def update_pdf_status(self, assessment_id: str, report_data: dict = None):
        """Update assessment PDF generation status"""
        try:
            update_data = {
                "pdf_generated": True
            }
            
            if report_data:
                update_data["report_data"] = report_data
            
            response = self.client.table(self.table_name).update(
                update_data
            ).eq("id", assessment_id).execute()
            
            return True
        except Exception as e:
            print(f"Error updating PDF status: {e}")
            return False
    
    def update_email_status(self, assessment_id: str):
        """Update assessment email sent status"""
        try:
            response = self.client.table(self.table_name).update({
                "email_sent": True
            }).eq("id", assessment_id).execute()
            
            return True
        except Exception as e:
            print(f"Error updating email status: {e}")
            return False
    
    def get_assessments_by_email(self, email: str):
        """Fetch all assessments for a specific email"""
        try:
            response = self.client.table(self.table_name).select("*").eq(
                "email", email
            ).order("created_at", desc=True).execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching assessments by email: {e}")
            return []