import spacy
from langdetect import detect, LangDetectException
import json
import random
import re

# Load spaCy models
try:
    nlp_en = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading 'en_core_web_sm' model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp_en = spacy.load("en_core_web_sm")

try:
    nlp_multi = spacy.load("xx_ent_wiki_sm")
except OSError:
    print("Downloading 'xx_ent_wiki_sm' model...")
    from spacy.cli import download
    download("xx_ent_wiki_sm")
    nlp_multi = spacy.load("xx_ent_wiki_sm")

# Load college data from JSON file
with open('college_data.json', 'r', encoding='utf-8') as f:
    college_data = json.load(f)
    print("College data loaded successfully!")

# --- Accessing data ---
college_name = college_data["college_name"]
departments = college_data["departments"]
leadership_info = college_data["leadership_info"]

def get_language(text):
    """Detect the language of the input text"""
    try:
        # Basic language detection
        detected = detect(text)
        
        # Check for Hindi/Devanagari script
        hindi_chars = re.findall(r'[\u0900-\u097F]', text)
        english_chars = re.findall(r'[a-zA-Z]', text)
        
        if hindi_chars and english_chars:
            return 'hinglish'
        elif hindi_chars:
            return 'hindi' 
        elif detected == 'hi':
            return 'hindi'
        else:
            return 'english'
    except LangDetectException:
        return 'english'  # default fallback

def get_intent_and_entities(text, language):
    """Extract intent and entities from text using spaCy NLP"""
    
    # Process text with appropriate model
    if language == 'english':
        doc = nlp_en(text.lower())
    else:
        doc = nlp_multi(text.lower())
    
    entities = {}
    
    # Extract named entities
    for ent in doc.ents:
        entities[ent.label_] = ent.text
    
    # Intent detection patterns
    intent_patterns = {
        'greeting': ['hello', 'hi', 'hey', 'good morning', 'good evening', 'namaste', 'namaskar', 'hola'],
        'fees': ['fees', 'fee', 'cost', 'price', 'charges', 'tuition', 'फीस', 'शुल्क', 'fees kya hai', 'kitni fees'],
        'admission': ['admission', 'apply', 'application', 'entrance', 'eligibility', 'दाखिला', 'प्रवेश', 'admission kaise', 'apply kaise'],
        'department': ['department', 'course', 'branch', 'engineering', 'computer', 'mechanical', 'civil', 'electrical', 'it', 'information technology', 'विभाग', 'कोर्स', 'computer engineering', 'mechanical engineering'],
        'faculty': ['faculty', 'teacher', 'professor', 'staff', 'hod', 'शिक्षक', 'प्रोफेसर', 'faculty kaun', 'teachers kaun'],
        'contact': ['contact', 'phone', 'email', 'address', 'location', 'संपर्क', 'पता', 'contact kaise', 'address kya'],
        'facilities': ['facilities', 'lab', 'library', 'hostel', 'canteen', 'sports', 'सुविधाएं', 'लैब', 'facilities kya'],
        'academics': ['academic', 'syllabus', 'curriculum', 'subjects', 'marks', 'exam', 'शैक्षणिक', 'पाठ्यक्रम', 'syllabus kya'],
        'placement': ['placement', 'job', 'career', 'company', 'package', 'salary', 'नौकरी', 'placement kaise', 'job kaise']
    }
    
    # Check for intent matches
    detected_intent = 'general'
    confidence = 0.5
    
    text_lower = text.lower()
    for intent, keywords in intent_patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_intent = intent
                confidence = 0.8 + (len(keyword) / len(text_lower)) * 0.2
                break
        if detected_intent != 'general':
            break
    
    # Enhanced entity extraction for departments
    department_mapping = {
        'computer': ['computer', 'cs', 'cse', 'computer science', 'computer engineering', 'कंप्यूटर'],
        'mechanical': ['mechanical', 'mech', 'mechanical engineering', 'मैकेनिकल'],
        'electrical': ['electrical', 'ee', 'electrical engineering', 'इलेक्ट्रिकल'],
        'civil': ['civil', 'civil engineering', 'सिविल'],
        'it': ['it', 'information technology', 'आईटी']
    }
    
    if detected_intent == 'department':
        for dept, variations in department_mapping.items():
            for variation in variations:
                if variation in text_lower:
                    entities['department'] = dept
                    confidence = 0.9
                    print(f"DEBUG: Department entity = '{dept}'")
                    break
            if 'department' in entities:
                break
    
    return detected_intent, entities, confidence

def generate_response(intent, entities, language, confidence):
    """Generate appropriate response based on intent, entities, and language"""
    
    # Select appropriate responses based on language
    if language == 'hindi':
        responses = college_data['hindi_responses']
    elif language == 'hinglish':
        responses = college_data['hinglish_responses']
    else:
        responses = college_data['english_responses']
    
    try:
        if intent == 'greeting':
            return responses['greeting']
        
        elif intent == 'fees':
            return responses['fees']
        
        elif intent == 'admission':
            return responses['admission']
        
        elif intent == 'department':
            if 'department' in entities:
                dept = entities['department']
                print(f"DEBUG: Available departments in responses = {list(responses['departments'].keys())}")
                if dept in responses['departments']:
                    return responses['departments'][dept]
                else:
                    return responses['departments']['overview']
            else:
                return responses['departments']['overview']
        
        elif intent == 'faculty':
            return responses['faculty']
        
        elif intent == 'contact':
            return responses['contact']
        
        elif intent == 'facilities':
            return responses['facilities']
        
        elif intent == 'academics':
            return responses['academics']
        
        elif intent == 'placement':
            return responses['placement']
        
        else:
            # Default response
            return responses.get('default', "I'm here to help you with college information. Please ask about admissions, fees, departments, or facilities.")
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try asking in a different way."