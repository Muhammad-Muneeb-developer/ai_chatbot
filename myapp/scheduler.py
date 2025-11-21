
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the background scheduler when Django starts"""
    scheduler = BackgroundScheduler()
    
    # Import here to avoid circular imports
    from .tasks import check_and_process_pending_assessments
    
    # Run every 2 minutes
    scheduler.add_job(
        check_and_process_pending_assessments,
        'interval',
        minutes=2,
        id='process_assessments',
        name='Process pending KI assessments',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Assessment scheduler started - checking every 2 minutes")