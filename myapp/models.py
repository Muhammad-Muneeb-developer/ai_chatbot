from django.db import models
import uuid

class AIAssessment(models.Model):
    """
    Model matching Supabase database schema
    """
    # Primary key - UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Contact & Company Info
    email = models.EmailField()
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    company_size = models.CharField(max_length=100)
    revenue = models.CharField(max_length=100)
    
    # Goals & Strategy
    main_goal = models.JSONField(default=list)  # ARRAY in PostgreSQL
    urgency = models.IntegerField()  # 1-5 scale
    budget = models.CharField(max_length=100)
    
    # Current Processes
    priority_processes = models.JSONField(default=list)
    pain_points = models.JSONField(default=list)
    detailed_challenges = models.TextField(blank=True)
    
    # Tools & Systems
    crm_system = models.CharField(max_length=255, blank=True)
    marketing_tools = models.JSONField(default=list)
    service_tools = models.JSONField(default=list)
    data_sources = models.JSONField(default=list)
    api_access = models.CharField(max_length=100, blank=True)
    
    # Current Metrics
    monthly_leads = models.IntegerField(null=True, blank=True)
    monthly_tickets = models.IntegerField(null=True, blank=True)
    recurring_tasks = models.JSONField(default=list)
    desired_outputs = models.JSONField(default=list)
    
    # Requirements
    data_privacy_importance = models.IntegerField()  # 1-5 scale
    languages = models.JSONField(default=list)
    success_metrics = models.JSONField(default=list)
    team_acceptance = models.IntegerField()  # 1-5 scale
    
    # Administrative
    responsible_person = models.CharField(max_length=255)
    consent_given = models.BooleanField(default=False)
    
    # Analysis Results
    calculated_score = models.IntegerField(null=True, blank=True)
    score_level = models.CharField(max_length=50, blank=True)
    analysis_completed = models.BooleanField(default=False)
    pdf_generated = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    # JSON Data Storage
    raw_answers = models.JSONField(default=dict, blank=True)
    chatgpt_analysis = models.JSONField(default=dict, blank=True)
    report_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_assessments'  # Match your Supabase table name
        ordering = ['-created_at']
        verbose_name = 'KI-Bewertung'
        verbose_name_plural = 'KI-Bewertungen'
    
    def __str__(self):
        return f"{self.company_name} - {self.email} ({self.created_at.date()})"
    
    def get_score_level(self):
        """Determine score level in German"""
        if self.calculated_score >= 80:
            return "Ausgezeichnet"
        elif self.calculated_score >= 60:
            return "Gut"
        elif self.calculated_score >= 40:
            return "Entwicklungsbedarf"
        else:
            return "Hohes Potenzial"