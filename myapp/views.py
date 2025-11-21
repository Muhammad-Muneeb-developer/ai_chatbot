"""
Assessment Processing Views
Uses modular ai_service.py and pdf_generator.py
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from .supabase_client import get_supabase
from .ai_service import get_ai_service
from .pdf_generator import generate_assessment_pdf
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# EXISTING VIEWS (Keep these as they are)
# ============================================================

def list_tables(request):
    """View to list all available tables in Supabase"""
    try:
        supabase = get_supabase()
        response = supabase.rpc('get_tables').execute()
        
        context = {
            'message': 'Available tables will be shown here',
            'tables': response.data if response.data else []
        }
        return render(request, 'tables_list.html', context)
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        context = {
            'message': 'Enter your table name manually',
            'error': str(e)
        }
        return render(request, 'tables_list.html', context)

def get_table_data(request, table_name):
    """Read data from any Supabase table (READ ONLY)"""
    try:
        supabase = get_supabase()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        response = supabase.table(table_name).select("*").limit(limit).offset(offset).execute()
        
        context = {
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data),
        }
        return render(request, 'table_data.html', context)
    
    except Exception as e:
        logger.error(f"Error reading from {table_name}: {str(e)}")
        return render(request, 'table_data.html', {
            'error': str(e),
            'table_name': table_name
        })

def get_table_data_json(request, table_name):
    """API endpoint to get table data as JSON"""
    try:
        supabase = get_supabase()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        response = supabase.table(table_name).select("*").limit(limit).offset(offset).execute()
        
        return JsonResponse({
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data)
        })
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def search_table(request, table_name):
    """Search/filter data in a table"""
    try:
        supabase = get_supabase()
        column = request.GET.get('column')
        value = request.GET.get('value')
        
        if column and value:
            response = supabase.table(table_name).select("*").eq(column, value).execute()
        else:
            response = supabase.table(table_name).select("*").limit(100).execute()
        
        context = {
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data),
            'search_column': column,
            'search_value': value
        }
        return render(request, 'table_data.html', context)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return render(request, 'table_data.html', {
            'error': str(e),
            'table_name': table_name
        })

# ============================================================
# NEW ASSESSMENT PROCESSING VIEWS
# ============================================================

def process_pending_assessments(request):
    """
    Process all pending assessments from ki_check_submissions table
    WHERE analysis_completed = false
    """
    try:
        supabase = get_supabase()
        
        # Get pending assessments
        response = supabase.table('ki_check_submissions').select('*').eq(
            'analysis_completed', False
        ).order('created_at', desc=False).limit(10).execute()
        
        if not response.data or len(response.data) == 0:
            return JsonResponse({
                'status': 'success',
                'message': 'Keine neuen Bewertungen zum Verarbeiten',
                'processed': 0
            })
        
        logger.info(f"Found {len(response.data)} pending assessments to process")
        
        results = []
        for assessment in response.data:
            try:
                success = process_single_assessment(assessment['id'])
                results.append({
                    'id': assessment['id'],
                    'company': assessment.get('company_name', 'N/A'),
                    'email': assessment.get('email', 'N/A'),
                    'status': 'success' if success else 'failed'
                })
            except Exception as e:
                logger.error(f"Error processing {assessment['id']}: {str(e)}")
                results.append({
                    'id': assessment['id'],
                    'company': assessment.get('company_name', 'N/A'),
                    'status': 'error',
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return JsonResponse({
            'status': 'success',
            'message': f'{success_count}/{len(results)} Bewertungen erfolgreich verarbeitet',
            'processed': len(results),
            'successful': success_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in process_pending_assessments: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def process_latest_assessment(request):
    """
    Process the most recent assessment (useful for testing)
    """
    try:
        supabase = get_supabase()
        
        # Get latest assessment
        response = supabase.table('ki_check_submissions').select('*').order(
            'created_at', desc=True
        ).limit(1).execute()
        
        if not response.data or len(response.data) == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Keine Bewertungen in der Datenbank gefunden'
            }, status=404)
        
        assessment = response.data[0]
        logger.info(f"Processing latest assessment: {assessment['id']}")
        
        success = process_single_assessment(assessment['id'])
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Bewertung erfolgreich verarbeitet!',
                'assessment_id': assessment['id'],
                'company': assessment.get('company_name', 'N/A'),
                'email': assessment.get('email', 'N/A'),
                'score': assessment.get('calculated_score', 'N/A')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Fehler bei der Verarbeitung der Bewertung'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in process_latest_assessment: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def process_assessment_by_id(request, assessment_id):
    """
    Process a specific assessment by ID
    """
    try:
        logger.info(f"Processing assessment by ID: {assessment_id}")
        
        success = process_single_assessment(assessment_id)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Bewertung erfolgreich verarbeitet',
                'assessment_id': assessment_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Fehler bei der Verarbeitung'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error processing assessment {assessment_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# ============================================================
# MAIN PROCESSING LOGIC
# ============================================================

def process_single_assessment(assessment_id):
    """
    Main workflow to process a single assessment
    
    Steps:
    1. Fetch data from Supabase
    2. Generate ChatGPT analysis (via ai_service.py)
    3. Generate PDF (via pdf_generator.py)
    4. Send email
    5. Update Supabase status
    
    Args:
        assessment_id (str): UUID of the assessment
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing Assessment: {assessment_id}")
        logger.info('='*60)
        
        supabase = get_supabase()
        
        # ===== STEP 1: FETCH DATA =====
        response = supabase.table('ki_check_submissions').select('*').eq(
            'id', assessment_id
        ).single().execute()
        
        if not response.data:
            logger.error(f"❌ Assessment {assessment_id} not found")
            return False
        
        assessment = response.data
        logger.info(f"✓ Fetched: {assessment.get('company_name', 'N/A')}")
        logger.info(f"  Email: {assessment.get('email', 'N/A')}")
        
        # ===== STEP 2: CHATGPT ANALYSIS =====
        if not assessment.get('analysis_completed', False):
            logger.info("⏳ Step 1/3: Generating ChatGPT analysis...")
            
            # Use ai_service.py
            ai_service = get_ai_service()
            analysis = ai_service.analyze_assessment(assessment)
            
            # Update Supabase with analysis
            supabase.table('ki_check_submissions').update({
                'calculated_score': analysis['score'],
                'score_level': analysis['score_level'],
                'chatgpt_analysis': analysis,
                'analysis_completed': True
            }).eq('id', assessment_id).execute()
            
            # Refresh data
            response = supabase.table('ki_check_submissions').select('*').eq(
                'id', assessment_id
            ).single().execute()
            assessment = response.data
            
            logger.info(f"✅ Analysis complete - Score: {analysis['score']}/100 ({analysis['score_level']})")
        else:
            logger.info("✓ Analysis already completed, skipping...")
        
        # ===== STEP 3: GENERATE PDF =====
        logger.info("⏳ Step 2/3: Generating professional PDF...")
        
        # Use pdf_generator.py
        pdf_buffer = generate_assessment_pdf(assessment)
        
        # Update PDF status
        supabase.table('ki_check_submissions').update({
            'pdf_generated': True,
            'report_data': {
                'generated_at': datetime.now().isoformat(),
                'score': assessment['calculated_score'],
                'score_level': assessment['score_level'],
                'pdf_size_kb': len(pdf_buffer) // 1024
            }
        }).eq('id', assessment_id).execute()
        
        logger.info(f"✅ PDF created ({len(pdf_buffer) // 1024}KB)")
        
        # ===== STEP 4: SEND EMAIL =====
        logger.info("⏳ Step 3/3: Sending email with PDF...")
        
        send_assessment_email(assessment, pdf_buffer)
        
        # Update email status
        supabase.table('ki_check_submissions').update({
            'email_sent': True
        }).eq('id', assessment_id).execute()
        
        logger.info(f"✅ Email sent to: {assessment['email']}")
        
        # ===== COMPLETE =====
        logger.info('='*60)
        logger.info("✅ SUCCESS! Assessment processing completed")
        logger.info('='*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ ERROR processing assessment {assessment_id}:")
        logger.error(f"   {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error('='*60 + "\n")
        return False

"""
Assessment Processing Views
Uses modular ai_service.py and pdf_generator.py
UPDATED WITH IMPROVED EMAIL HANDLING AND ERROR LOGGING
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from .supabase_client import get_supabase
from .ai_service import get_ai_service
from .pdf_generator import generate_assessment_pdf
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

# ============================================================
# EXISTING VIEWS (Keep these as they are)
# ============================================================

def list_tables(request):
    """View to list all available tables in Supabase"""
    try:
        supabase = get_supabase()
        response = supabase.rpc('get_tables').execute()
        
        context = {
            'message': 'Available tables will be shown here',
            'tables': response.data if response.data else []
        }
        return render(request, 'tables_list.html', context)
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        context = {
            'message': 'Enter your table name manually',
            'error': str(e)
        }
        return render(request, 'tables_list.html', context)

def get_table_data(request, table_name):
    """Read data from any Supabase table (READ ONLY)"""
    try:
        supabase = get_supabase()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        response = supabase.table(table_name).select("*").limit(limit).offset(offset).execute()
        
        context = {
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data),
        }
        return render(request, 'table_data.html', context)
    
    except Exception as e:
        logger.error(f"Error reading from {table_name}: {str(e)}")
        return render(request, 'table_data.html', {
            'error': str(e),
            'table_name': table_name
        })

def get_table_data_json(request, table_name):
    """API endpoint to get table data as JSON"""
    try:
        supabase = get_supabase()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        response = supabase.table(table_name).select("*").limit(limit).offset(offset).execute()
        
        return JsonResponse({
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data)
        })
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def search_table(request, table_name):
    """Search/filter data in a table"""
    try:
        supabase = get_supabase()
        column = request.GET.get('column')
        value = request.GET.get('value')
        
        if column and value:
            response = supabase.table(table_name).select("*").eq(column, value).execute()
        else:
            response = supabase.table(table_name).select("*").limit(100).execute()
        
        context = {
            'table_name': table_name,
            'data': response.data,
            'count': len(response.data),
            'search_column': column,
            'search_value': value
        }
        return render(request, 'table_data.html', context)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return render(request, 'table_data.html', {
            'error': str(e),
            'table_name': table_name
        })

# ============================================================
# NEW: EMAIL TESTING VIEW
# ============================================================

def test_email(request):
    """
    Test email configuration - Use this first to verify email works
    Access via: http://localhost:8000/test-email/
    """
    try:
        from django.core.mail import send_mail
        
        logger.info("🧪 Testing email configuration...")
        logger.info(f"   From: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"   Host: {settings.EMAIL_HOST}")
        logger.info(f"   Port: {settings.EMAIL_PORT}")
        
        result = send_mail(
            subject='✅ Test Email from Django - KI Readiness System',
            message='This is a test email to verify SMTP configuration.\n\nIf you receive this, your email setup is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Send to yourself
            fail_silently=False,
        )
        
        logger.info(f"✅ Test email sent successfully! Result: {result}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Test email sent successfully! Check your inbox.',
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'smtp_host': settings.EMAIL_HOST,
            'smtp_port': settings.EMAIL_PORT
        })
        
    except Exception as e:
        logger.error(f"❌ Email test failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'status': 'error',
            'message': f'Email test failed: {str(e)}',
            'error_details': traceback.format_exc()
        }, status=500)

# ============================================================
# NEW ASSESSMENT PROCESSING VIEWS
# ============================================================

def process_pending_assessments(request):
    """
    Process all pending assessments from ki_check_submissions table
    WHERE analysis_completed = false
    """
    try:
        supabase = get_supabase()
        
        # Get pending assessments
        response = supabase.table('ki_check_submissions').select('*').eq(
            'analysis_completed', False
        ).order('created_at', desc=False).limit(10).execute()
        
        if not response.data or len(response.data) == 0:
            return JsonResponse({
                'status': 'success',
                'message': 'Keine neuen Bewertungen zum Verarbeiten',
                'processed': 0
            })
        
        logger.info(f"Found {len(response.data)} pending assessments to process")
        
        results = []
        for assessment in response.data:
            try:
                success = process_single_assessment(assessment['id'])
                results.append({
                    'id': assessment['id'],
                    'company': assessment.get('company_name', 'N/A'),
                    'email': assessment.get('email', 'N/A'),
                    'status': 'success' if success else 'failed'
                })
            except Exception as e:
                logger.error(f"Error processing {assessment['id']}: {str(e)}")
                results.append({
                    'id': assessment['id'],
                    'company': assessment.get('company_name', 'N/A'),
                    'status': 'error',
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return JsonResponse({
            'status': 'success',
            'message': f'{success_count}/{len(results)} Bewertungen erfolgreich verarbeitet',
            'processed': len(results),
            'successful': success_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in process_pending_assessments: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def process_latest_assessment(request):
    """
    Process the most recent assessment (useful for testing)
    """
    try:
        supabase = get_supabase()
        
        # Get latest assessment
        response = supabase.table('ki_check_submissions').select('*').order(
            'created_at', desc=True
        ).limit(1).execute()
        
        if not response.data or len(response.data) == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Keine Bewertungen in der Datenbank gefunden'
            }, status=404)
        
        assessment = response.data[0]
        logger.info(f"Processing latest assessment: {assessment['id']}")
        
        success = process_single_assessment(assessment['id'])
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Bewertung erfolgreich verarbeitet!',
                'assessment_id': assessment['id'],
                'company': assessment.get('company_name', 'N/A'),
                'email': assessment.get('email', 'N/A'),
                'score': assessment.get('calculated_score', 'N/A')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Fehler bei der Verarbeitung der Bewertung'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in process_latest_assessment: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def process_assessment_by_id(request, assessment_id):
    """
    Process a specific assessment by ID
    """
    try:
        logger.info(f"Processing assessment by ID: {assessment_id}")
        
        success = process_single_assessment(assessment_id)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Bewertung erfolgreich verarbeitet',
                'assessment_id': assessment_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Fehler bei der Verarbeitung'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error processing assessment {assessment_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# ============================================================
# MAIN PROCESSING LOGIC - UPDATED WITH BETTER ERROR HANDLING
# ============================================================

def process_single_assessment(assessment_id):
    """
    FIXED VERSION: Removes references to non-existent columns
    """
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing Assessment: {assessment_id}")
        logger.info('='*60)
        
        supabase = get_supabase()
        
        # ===== STEP 1: FETCH DATA =====
        response = supabase.table('ki_check_submissions').select('*').eq(
            'id', assessment_id
        ).single().execute()
        
        if not response.data:
            logger.error(f"❌ Assessment {assessment_id} not found")
            return False
        
        assessment = response.data
        logger.info(f"✓ Fetched: {assessment.get('company_name', 'N/A')}")
        logger.info(f"  Email: {assessment.get('email', 'N/A')}")
        
        # Check if already processed
        if assessment.get('email_sent', False):
            logger.info("✓ Email already sent, skipping...")
            return True
        
        # ===== STEP 2: CHATGPT ANALYSIS =====
        if not assessment.get('analysis_completed', False):
            logger.info("⏳ Step 1/3: Generating ChatGPT analysis...")
            
            try:
                from .ai_service import get_ai_service
                
                ai_service = get_ai_service()
                analysis = ai_service.analyze_assessment(assessment)
                
                # FIXED: Only update columns that exist
                supabase.table('ki_check_submissions').update({
                    'calculated_score': analysis['score'],
                    'score_level': analysis['score_level'],
                    'chatgpt_analysis': analysis,
                    'analysis_completed': True
                }).eq('id', assessment_id).execute()
                
                # Refresh data
                response = supabase.table('ki_check_submissions').select('*').eq(
                    'id', assessment_id
                ).single().execute()
                assessment = response.data
                
                logger.info(f"✅ Analysis complete - Score: {analysis['score']}/100 ({analysis['score_level']})")
                
            except Exception as e:
                logger.error(f"❌ ChatGPT analysis failed: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        else:
            logger.info("✓ Analysis already completed, skipping...")
        
        # ===== STEP 3: GENERATE PDF =====
        logger.info("⏳ Step 2/3: Generating professional PDF...")
        
        try:
            from .pdf_generator import generate_assessment_pdf
            
            pdf_buffer = generate_assessment_pdf(assessment)
            
            # FIXED: Only update columns that exist
            supabase.table('ki_check_submissions').update({
                'pdf_generated': True
            }).eq('id', assessment_id).execute()
            
            logger.info(f"✅ PDF created ({len(pdf_buffer) // 1024}KB)")
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        # ===== STEP 4: SEND EMAIL =====
        logger.info("⏳ Step 3/3: Sending email with PDF...")
        
        try:
            from .views import send_assessment_email
            
            email_sent = send_assessment_email(assessment, pdf_buffer)
            
            if email_sent:
                # FIXED: Only update email_sent (which exists)
                supabase.table('ki_check_submissions').update({
                    'email_sent': True
                }).eq('id', assessment_id).execute()
                
                logger.info(f"✅ Email sent successfully to {assessment.get('email')}")
            else:
                logger.error(f"❌ Failed to send email")
                # Mark as not sent so it can be retried
                supabase.table('ki_check_submissions').update({
                    'email_sent': False
                }).eq('id', assessment_id).execute()
                
        except Exception as e:
            logger.error(f"❌ Email sending exception: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Mark as failed
            supabase.table('ki_check_submissions').update({
                'email_sent': False
            }).eq('id', assessment_id).execute()
            
            # Don't fail entire process for email errors
            logger.warning("⚠️  Continuing despite email error")
        
        # ===== COMPLETE =====
        logger.info('='*60)
        logger.info("✅ SUCCESS! Assessment processing completed")
        logger.info('='*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ ERROR processing assessment {assessment_id}:")
        logger.error(f"   {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error('='*60 + "\n")
        return False


# ============================================================
# EMAIL SENDING FUNCTION - COMPLETELY REWRITTEN
# ============================================================

def send_assessment_email(assessment, pdf_buffer):
    """
    Send email with PDF attachment
    Returns True if successful, False otherwise
    """
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        score = assessment.get('calculated_score', 0)
        score_level = assessment.get('score_level', 'N/A')
        company_name = assessment.get('company_name', 'Ihr Unternehmen')
        recipient_email = assessment.get('email', '')
        
        if not recipient_email:
            logger.error("❌ No recipient email found")
            return False
        
        logger.info(f"   📧 Sending to: {recipient_email}")
        
        subject = f"Ihre KI-Readiness-Bewertung - Score: {score}/100 - {company_name}"
        
        body = f"""
Sehr geehrte Damen und Herren,

vielen Dank für Ihre Teilnahme an der KI-Readiness-Bewertung.

Ihre Ergebnisse:
• Unternehmen: {company_name}
• KI-Readiness-Score: {score}/100
• Bewertung: {score_level}

Das beigefügte PDF enthält Ihre detaillierte Analyse und Handlungsempfehlungen.

Mit freundlichen Grüßen
Ihr KI-Readiness Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        
        filename = f"KI_Readiness_{company_name.replace(' ', '_')}.pdf"
        email.attach(filename, pdf_buffer, 'application/pdf')
        
        result = email.send(fail_silently=False)
        
        if result == 1:
            logger.info(f"   ✅ Email sent successfully to {recipient_email}")
            return True
        else:
            logger.error(f"   ❌ Email send failed")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Email error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False









from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt  # Required for external webhooks
@require_http_methods(["POST"])
def webhook_new_assessment(request):
    """
    Webhook endpoint that processes assessment immediately on form submission
    
    INSTANT WORKFLOW:
    1. User submits form
    2. Your website calls this webhook
    3. Assessment processed immediately
    4. Email sent within 5-10 seconds
    
    Usage from your website:
    POST http://your-django-server.com/webhook/new-assessment/
    Body: {"assessment_id": "uuid-here"}
    """
    try:
        # Parse request
        data = json.loads(request.body)
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return JsonResponse({
                'status': 'error',
                'message': 'assessment_id required'
            }, status=400)
        
        logger.info(f"🔔 WEBHOOK TRIGGERED: New assessment {assessment_id}")
        
        # Process immediately
        success = process_single_assessment(assessment_id)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Assessment processed and email sent',
                'assessment_id': assessment_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Processing failed'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
