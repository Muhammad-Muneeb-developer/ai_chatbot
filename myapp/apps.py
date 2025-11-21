# myapp/apps.py
# CORRECTED VERSION - matches the new tasks.py structure

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        """
        Start background scheduler when Django starts
        This runs automatically when Django loads the app
        """
        import sys
        
        # Only start in the main process, not in the reloader process
        # This prevents the scheduler from starting twice
        if 'runserver' in sys.argv and '--noreload' not in sys.argv:
            # Check if this is the reloader process
            import os
            if os.environ.get('RUN_MAIN') != 'true':
                logger.info("⏭️  Skipping scheduler in reloader process")
                return
        
        try:
            # Import the correct function from tasks.py
            from .tasks import start_assessment_processor
            
            # Start the background processor
            start_assessment_processor()
            
            logger.info("✅ Assessment email scheduler started successfully!")
            print("✅ Assessment email scheduler started successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {str(e)}")
            print(f"❌ Failed to start scheduler: {str(e)}")
            # Don't crash Django if scheduler fails
            import traceback
            traceback.print_exc()