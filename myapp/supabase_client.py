"""
Supabase Client for Read-Only Database Access
Place this file in: myapp/supabase_client.py
"""
from supabase import create_client, Client
from django.conf import settings

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance
    
    def get_client(self) -> Client:
        return self.client

# Helper function to get Supabase client
def get_supabase() -> Client:
    return SupabaseClient().get_client()