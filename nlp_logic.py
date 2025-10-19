import spacy
from langdetect import detect, LangDetectException
import json
import random

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

# --- Accessing data ---
college_name = college_data["college_name"]
departments = college_data["departments"]
leadership_info = college_data["leadership_info"]
department_details = college_data["department_details"]
faculty_data = college_data["faculty_data"]
responses = college_data["responses"]
hindi_responses = college_data["hindi_responses"]
hinglish_responses = college_data["hinglish_responses"]

def get_language(text):
    """Detects the language of the given text."""
    try:
        lang = detect(text)
        if lang.startswith('en'):
            return 'en'
        elif lang.startswith('hi'):
            # Check for Hinglish keywords
            if any(word in text.lower() for word in ["kaise", "kya", "hai", "college", "admission"]):
                return 'hinglish'
            return 'hi'
    except LangDetectException:
        return 'en'  # Default to English
    return 'en'

def get_intent_and_entities(text, lang):
    """Extracts intent and entities from the text using spaCy."""
    nlp = nlp_en if lang == 'en' else nlp_multi
    doc = nlp(text)
    
    intent = "unknown"
    entities = {ent.label_: ent.text for ent in doc.ents}

    # Simple keyword-based intent detection
    text_lower = text.lower()
    if any(word in text_lower for word in ["fee", "fees", "structure"]):
        intent = "fees"
    elif any(word in text_lower for word in ["admission", "apply", "process"]):
        intent = "admission"
    elif any(word in text_lower for word in ["department", "branch"]):
        intent = "department_info"
    elif any(word in text_lower for word in ["faculty", "teacher", "professor"]):
        intent = "faculty"
    elif any(word in text_lower for word in ["contact", "address", "phone", "email"]):
        intent = "contact"
    elif any(word in text_lower for word in ["hello", "hi", "hey", "namaste"]):
        intent = "greeting"

    # Extract department entity if not found by NER
    if "department" not in entities:
        for dept in departments:
            if dept.lower() in text_lower:
                entities["department"] = dept
                break

    return intent, entities

def generate_response(intent, entities, lang):
    """Generates a response based on intent, entities, and language."""
    if lang == 'hi':
        response_dict = hindi_responses
    elif lang == 'hinglish':
        response_dict = hinglish_responses
    else:
        response_dict = responses

    if intent == "greeting":
        return random.choice(response_dict.get("greeting", responses["greeting"]))

    if intent == "fees":
        return response_dict.get("fees", {}).get("overview", responses["fees"]["overview"])

    if intent == "admission":
        return response_dict.get("admission_info", responses["admission_info"])

    if intent == "contact":
        return response_dict.get("contact_details", responses["contact_details"])

    if intent == "department_info":
        dept_entity = entities.get("department")
        if dept_entity:
            dept_key = dept_entity.lower().replace(" engineering", "")
            return department_details.get(dept_key, {}).get("about", "Department details not found.")
        return response_dict.get("department_info", responses["department_info"])

    if intent == "faculty":
        dept_entity = entities.get("department")
        if dept_entity:
            dept_key = dept_entity.lower().replace(" engineering", "").replace("science ", "").replace("it ", "it")
            faculty_list = faculty_data.get(dept_key)
            if faculty_list:
                response = f"<strong>Faculty of {dept_entity}:</strong><br>"
                for member in faculty_list:
                    response += f"- {member['name']}, {member['position']}<br>"
                return response
        return "Please specify a department to see the faculty list."

    # Fallback response
    return random.choice(response_dict.get("default", responses["default"]))
