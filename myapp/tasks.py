# myapp/tasks.py
# Background scheduler for processing assessments automatically

import time
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class AssessmentProcessor:
    """
    Background processor that checks for new assessments every 30 seconds
    and processes them automatically
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        logger.info("🔧 AssessmentProcessor initialized")
    
    def start(self):
        """Start the background processor thread"""
        if self.running:
            logger.warning("⚠️  Processor already running, skipping start")
            return
        
        self.running = True
        self.thread = Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info("🚀 Background assessment processor thread started")
        print("🚀 Background assessment processor thread started")
    
    def stop(self):
        """Stop the background processor"""
        self.running = False
        if self.thread:
            logger.info("🛑 Assessment processor stopping...")
            print("🛑 Assessment processor stopping...")
    
    def _process_loop(self):
        """
        Main processing loop
        Checks every 30 seconds for new assessments
        """
        logger.info("♻️  Processing loop started - checking every 30 seconds")
        
        while self.running:
            try:
                logger.info("🔍 Checking for new assessments...")
                self._check_and_process()
                
            except Exception as e:
                logger.error(f"❌ Error in processing loop: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Wait 30 seconds before next check
            if self.running:  # Check if still running before sleeping
                logger.info("⏳ Waiting 30 seconds until next check...")
                time.sleep(30)
        
        logger.info("✋ Processing loop stopped")
    
    def _check_and_process(self):
        """
        Check for NEW unprocessed assessments and process them
        Only processes records where email_sent = false OR null
        """
        try:
            from .supabase_client import get_supabase
            from .views import process_single_assessment
            
            supabase = get_supabase()
            
            # CRITICAL QUERY: Only get NEW unprocessed assessments
            # This prevents re-sending emails to users who already received them
            response = supabase.table('ki_check_submissions').select(
                'id, email, company_name, email_sent, created_at'
            ).or_(
                'email_sent.is.null,email_sent.eq.false'
            ).order('created_at', desc=False).limit(5).execute()
            
            # Check if any new assessments found
            if not response.data or len(response.data) == 0:
                logger.info("✓ No new assessments to process")
                print("✓ No new assessments to process")
                return
            
            # Found new assessments to process
            count = len(response.data)
            logger.info(f"📋 Found {count} NEW assessment(s) to process")
            print(f"📋 Found {count} NEW assessment(s) to process")
            
            # Process each NEW assessment
            for idx, assessment in enumerate(response.data, 1):
                if not self.running:  # Stop if processor was stopped
                    logger.info("Processor stopped, aborting current batch")
                    break
                
                assessment_id = assessment['id']
                
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 Processing {idx}/{count}: {assessment_id[:8]}...")
                logger.info(f"   Company: {assessment.get('company_name', 'N/A')}")
                logger.info(f"   Email: {assessment.get('email', 'N/A')}")
                print(f"🔄 Processing: {assessment.get('company_name', 'N/A')}")
                
                try:
                    # Process the assessment
                    success = process_single_assessment(assessment_id)
                    
                    if success:
                        logger.info(f"✅ Successfully processed: {assessment_id[:8]}")
                        print(f"✅ Successfully processed: {assessment.get('company_name', 'N/A')}")
                    else:
                        logger.error(f"❌ Failed to process: {assessment_id[:8]}")
                        print(f"❌ Failed to process: {assessment_id[:8]}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {assessment_id[:8]}: {str(e)}")
                    print(f"❌ Failed to process: {assessment_id[:8]}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
                
                # Small delay between processing to avoid overwhelming the system
                time.sleep(2)
            
            logger.info(f"{'='*60}\n")
            logger.info(f"✅ Batch processing complete - processed {count} assessment(s)")
            print(f"✅ Batch processing complete")
                
        except Exception as e:
            logger.error(f"❌ Error checking assessments: {str(e)}")
            print(f"❌ Error checking assessments: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


# ============================================================
# GLOBAL PROCESSOR INSTANCE
# ============================================================

_processor = None

def start_assessment_processor():
    """
    Start the background assessment processor
    Called from apps.py when Django starts
    """
    global _processor
    
    if _processor is None:
        logger.info("Creating new AssessmentProcessor instance")
        _processor = AssessmentProcessor()
    
    _processor.start()
    return _processor

def stop_assessment_processor():
    """
    Stop the background assessment processor
    Can be called to gracefully shutdown
    """
    global _processor
    if _processor:
        _processor.stop()

def get_processor_status():
    """
    Get the current status of the processor
    Useful for monitoring
    """
    global _processor
    if _processor:
        return {
            'running': _processor.running,
            'thread_alive': _processor.thread.is_alive() if _processor.thread else False
        }
    return {'running': False, 'thread_alive': False}