from openai import OpenAI
from typing import Dict, Any
import os
from dotenv import load_dotenv
import json

load_dotenv()

class AIReadinessService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def _extract_text_from_raw(self, raw_value):
        """Extract text from raw_answers format"""
        if isinstance(raw_value, dict) and 'text' in raw_value:
            return raw_value['text']
        elif isinstance(raw_value, list):
            return [item.get('text', str(item)) if isinstance(item, dict) else str(item) for item in raw_value]
        return str(raw_value) if raw_value else 'N/A'
    
    def _extract_values_from_raw(self, raw_value):
        """Extract values (ratings) from raw_answers format"""
        if isinstance(raw_value, list):
            values = []
            for item in raw_value:
                if isinstance(item, dict):
                    if 'text' in item:
                        text = item['text']
                        value = item.get('value', 0)
                        values.append(f"{text} (Bewertung: {value})")
            return values if values else [str(item) for item in raw_value]
        return []
    
    def analyze_assessment(self, assessment_data: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Main method to analyze assessment data
        This is called from your views
        """
        return self.analyze_from_supabase(assessment_data)
    
    def analyze_from_supabase(self, assessment_data: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Analyze assessment data from Supabase and generate comprehensive report in German
        """
        
        # Extract raw_answers for more detailed analysis
        raw_answers = assessment_data.get('raw_answers', {})
        
        # Build comprehensive prompt from Supabase data
        prompt = f"""Analysiere diese umfassende KI-Readiness-Bewertung und erstelle einen detaillierten Bericht AUF DEUTSCH.

UNTERNEHMENSDATEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Unternehmensname: {assessment_data.get('company_name', 'N/A')}
• Branche: {assessment_data.get('industry') or 'Nicht angegeben'}
• Unternehmensgröße: {assessment_data.get('company_size') or 'Nicht angegeben'}
• Umsatz: {assessment_data.get('revenue') or 'Nicht angegeben'}

HAUPTZIELE & STRATEGIE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Hauptziele mit Priorität: {', '.join(self._extract_values_from_raw(raw_answers.get('mainGoal', [])))}
• Dringlichkeit: {assessment_data.get('urgency') or 'Nicht angegeben'}
• Budget: {assessment_data.get('budget') or 'Nicht angegeben'}
• Verantwortliche Person: {assessment_data.get('responsible_person') or 'Nicht angegeben'}

AKTUELLE PROZESSE & HERAUSFORDERUNGEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Prioritätsprozesse mit Bewertung: {', '.join(self._extract_values_from_raw(raw_answers.get('priorityProcesses', [])))}
• Schmerzpunkte mit Intensität: {', '.join(self._extract_values_from_raw(raw_answers.get('painPoints', [])))}
• Detaillierte Herausforderungen: {self._extract_text_from_raw(raw_answers.get('detailedChallenges', 'N/A'))}
• Wiederkehrende Aufgaben mit Häufigkeit: {', '.join(self._extract_values_from_raw(raw_answers.get('recurringTasks', [])))}

TECHNOLOGIE-STACK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• CRM-System: {assessment_data.get('crm_system') or 'Keines'}
• Marketing-Tools mit Nutzungsintensität: {', '.join(self._extract_values_from_raw(raw_answers.get('marketingTools', [])))}
• Service-Tools mit Nutzungsintensität: {', '.join(self._extract_values_from_raw(raw_answers.get('serviceTools', [])))}
• Datenquellen mit Wichtigkeit: {', '.join(self._extract_values_from_raw(raw_answers.get('dataSources', [])))}
• API-Zugang: {assessment_data.get('api_access') or 'Nicht angegeben'}

AKTUELLE METRIKEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Monatliche Leads: {assessment_data.get('monthly_leads', 'N/A')}
• Monatliche Tickets: {assessment_data.get('monthly_tickets', 'N/A')}
• Gewünschte Ergebnisse mit Priorität: {', '.join(self._extract_values_from_raw(raw_answers.get('desiredOutputs', [])))}

ANFORDERUNGEN & PRÄFERENZEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Datenschutz-Wichtigkeit: {assessment_data.get('data_privacy_importance') or 'Nicht angegeben'}
• Sprachen mit Wichtigkeit: {', '.join(self._extract_values_from_raw(raw_answers.get('languages', [])))}
• Erfolgsmetriken mit Priorität: {', '.join(self._extract_values_from_raw(raw_answers.get('successMetrics', [])))}
• Team-Akzeptanz: {assessment_data.get('team_acceptance') or 'Nicht angegeben'}

ZUSÄTZLICHE INFORMATIONEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Bisherige Erfahrung: {raw_answers.get('previousExperience', 'Nicht angegeben')}
• Gewünschte Implementierungsgeschwindigkeit: {raw_answers.get('implementationSpeed', 'Nicht angegeben')}
• Größte Sorge: {raw_answers.get('biggestConcern', 'Nicht angegeben')}
• Zusätzliche Infos: {self._extract_text_from_raw(raw_answers.get('additionalInfo', 'Keine'))}

WICHTIG: 
- Der Score {assessment_data.get('calculated_score', 50)} wurde bereits berechnet (0-100 Skala)
- Berücksichtige die Bewertungen (value) in den Antworten - höhere Werte bedeuten höhere Priorität/Intensität
- Erstelle eine VOLLSTÄNDIGE Analyse AUF DEUTSCH

Analysiere basierend auf allen bereitgestellten Informationen:
1. Die aktuelle digitale Reife und KI-Bereitschaft (nutze den Score {assessment_data.get('calculated_score', 50)})
2. Konkrete Stärken basierend auf hohen Bewertungen (value >= 4)
3. Verbesserungsbereiche basierend auf niedrigen Bewertungen
4. Spezifische KI-Anwendungsfälle, die zu den priorisierten Prozessen passen
5. Sofort umsetzbare Quick Wins (3-6 Monate) basierend auf wiederkehrenden Aufgaben
6. Langfristige strategische Schritte
7. Konkrete Empfehlungen basierend auf Budget, Dringlichkeit und Team-Akzeptanz

Gib deine Antwort als JSON-Objekt mit folgenden Feldern zurück:

{{
  "score": {assessment_data.get('calculated_score', 50)} (übernimm diesen Wert),
  "score_level": "Hoch" | "Mittel" | "Niedrig" (basierend auf Score: >=70=Hoch, 40-69=Mittel, <40=Niedrig),
  "executive_summary": "2-3 Sätze Zusammenfassung auf Deutsch, die die Hauptstärken und wichtigsten Handlungsfelder hervorhebt",
  "strengths": ["Konkrete Stärke 1", "Konkrete Stärke 2", ...] (4-6 Punkte auf Deutsch, fokussiere auf Bereiche mit hohen Bewertungen),
  "weaknesses": ["Konkrete Schwäche 1", "Konkrete Schwäche 2", ...] (4-6 Punkte auf Deutsch, fokussiere auf Lücken und niedrige Bewertungen),
  "recommended_use_cases": [
    {{
      "title": "Präziser Titel des Use Case",
      "description": "Detaillierte Beschreibung wie dieser Use Case das Unternehmen konkret unterstützt",
      "impact": "Konkreter erwarteter Impact mit Zahlen wenn möglich",
      "effort": "Gering" | "Mittel" | "Hoch",
      "priority": "Sofort" | "Kurzfristig" | "Langfristig"
    }},
    ... (6-8 Use Cases, priorisiert nach den Hauptzielen)
  ],
  "quick_wins": [
    {{
      "title": "Konkreter Quick Win Titel",
      "description": "Detaillierte Beschreibung was genau zu tun ist",
      "timeframe": "Konkreter Zeitrahmen (z.B. 2-3 Monate)",
      "expected_benefit": "Konkreter erwarteter Nutzen mit messbaren Ergebnissen"
    }},
    ... (4-6 Quick Wins)
  ],
  "strategic_steps": [
    {{
      "phase": "Phase 1: Aussagekräftiger Name",
      "description": "Detaillierte Beschreibung der Phase",
      "timeframe": "Konkreter Zeitrahmen",
      "key_actions": ["Konkrete Aktion 1", "Konkrete Aktion 2", ...]
    }},
    ... (3-4 Phasen)
  ],
  "budget_recommendation": "Konkrete Budget-Empfehlung mit Aufschlüsselung nach Phasen, wenn Budget angegeben wurde",
  "next_actions": ["Nächster konkreter Schritt mit Verantwortlichkeit"] (4-5 Punkte)
}}

Gib NUR das JSON-Objekt zurück, keinen anderen Text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "Du bist ein erfahrener KI-Strategieberater mit Expertise in digitaler Transformation und Geschäftsprozessoptimierung. Du analysierst Bewertungsskalen genau und gibst präzise, umsetzbare Empfehlungen. Antworte IMMER auf Deutsch und nur mit validem JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure score_level is set correctly for new scale
            if 'score' in result:
                score = result['score']
                if score >= 70:
                    result['score_level'] = "Hoch"
                elif score >= 40:
                    result['score_level'] = "Mittel"
                else:
                    result['score_level'] = "Niedrig"
            
            return result
            
        except Exception as e:
            print(f"Error in ChatGPT analysis: {str(e)}")
            return self._get_fallback_analysis(assessment_data)
    
    def _get_fallback_analysis(self, assessment_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Fallback analysis if ChatGPT fails"""
        score = assessment_data.get('calculated_score', 50)
        
        if score >= 70:
            score_level = "Hoch"
        elif score >= 40:
            score_level = "Mittel"
        else:
            score_level = "Niedrig"
        
        return {
            "score": score,
            "score_level": score_level,
            "executive_summary": f"Analyse für {assessment_data.get('company_name', 'Ihr Unternehmen')} wurde erstellt. Mit einem Score von {score}/100 besteht gutes Potenzial für KI-Implementierung.",
            "strengths": [
                "Klare Zieldefinition vorhanden",
                "Grundlegende digitale Infrastruktur etabliert",
                "Bewusstsein für Optimierungsbedarf erkennbar",
                "Bereitschaft zur digitalen Transformation vorhanden"
            ],
            "weaknesses": [
                "Automatisierungspotenzial noch nicht ausgeschöpft",
                "Datenintegration kann verbessert werden",
                "KI-Expertise sollte aufgebaut werden",
                "Prozesse könnten stärker standardisiert sein"
            ],
            "recommended_use_cases": [
                {
                    "title": "Automatisierte Lead-Qualifizierung",
                    "description": "KI-basierte Bewertung eingehender Leads anhand von Verhaltensdaten",
                    "impact": "30% Zeitersparnis im Vertrieb",
                    "effort": "Mittel",
                    "priority": "Kurzfristig"
                },
                {
                    "title": "Intelligenter Chatbot für Kundenservice",
                    "description": "24/7 Erstberatung und FAQ-Beantwortung",
                    "impact": "40% Reduzierung der Support-Anfragen",
                    "effort": "Mittel",
                    "priority": "Sofort"
                }
            ],
            "quick_wins": [
                {
                    "title": "Automatisierte Datenübertragung",
                    "description": "Implementierung von API-Verbindungen zwischen bestehenden Systemen",
                    "timeframe": "2-3 Monate",
                    "expected_benefit": "Eliminierung manueller Dateneingabe, 20% Zeitersparnis"
                }
            ],
            "strategic_steps": [
                {
                    "phase": "Phase 1: Grundlagen schaffen (0-3 Monate)",
                    "description": "Aufbau der technischen Basis",
                    "timeframe": "3 Monate",
                    "key_actions": ["Daten konsolidieren", "APIs einrichten", "Team schulen"]
                }
            ],
            "budget_recommendation": "Empfohlenes Startbudget: 5.000-15.000€ für erste Implementierungen und Proof-of-Concepts",
            "next_actions": [
                "Detailanalyse der wichtigsten Prozesse durchführen",
                "Pilotprojekt für Quick Win auswählen",
                "Internes KI-Team zusammenstellen",
                "Technologie-Partner evaluieren"
            ]
        }


# Singleton instance
_ai_service_instance = None

def get_ai_service() -> AIReadinessService:
    """
    Get singleton instance of AIReadinessService
    This function is imported in your views.py
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIReadinessService()
    return _ai_service_instance