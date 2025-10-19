from flask import Flask, render_template, request, jsonify
import random
import spacy
from langdetect import detect, LangDetectException
import json
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

# Load college data
try:
    with open('college_data.json', 'r', encoding='utf-8') as f:
        college_data = json.load(f)
    print("College data loaded successfully!")
except FileNotFoundError:
    print("Warning: college_data.json not found.")
    college_data = {}

app = Flask(__name__)

def get_language(text):
    """Enhanced language detection with better accuracy"""
    try:
        # Check for Hindi/Devanagari script
        hindi_chars = re.findall(r'[\u0900-\u097F]', text)
        english_chars = re.findall(r'[a-zA-Z]', text)
        
        # Check for Hinglish indicators
        hinglish_indicators = ["kaise", "kya", "kab", "kitna", "hai", "hoon", "main", "aap", 
                             "college", "admission", "fees", "batao", "bolo", "btao", "kya hai",
                             "ke baare mein", "baare mein", "kaun hain"]
        
        if hindi_chars and english_chars:
            return 'hinglish'
        elif any(word in text.lower() for word in hinglish_indicators):
            return 'hinglish'
        elif hindi_chars:
            return 'hindi'
        else:
            # Use langdetect for other languages
            detected = detect(text)
            if detected == 'hi':
                return 'hindi'
            else:
                return 'english'
    except (LangDetectException, Exception):
        return 'english'  # Default to English

def get_intent_and_entities(text, language):
    """Advanced intent recognition and entity extraction"""
    # Process text with appropriate model
    if language == 'english':
        doc = nlp_en(text.lower())
    else:
        doc = nlp_multi(text.lower())
    
    entities = {}
    
    # Extract named entities
    for ent in doc.ents:
        entities[ent.label_] = ent.text
    
    # Enhanced intent detection with confidence scoring
    text_lower = text.lower()
    intent = "general"
    confidence = 0.5
    
    # Greeting patterns (multilingual)
    greeting_patterns = ["hello", "hi", "hey", "namaste", "good morning", "good afternoon", 
                        "good evening", "hii", "helo", "kaise ho", "kya haal", "sup"]
    if any(pattern in text_lower for pattern in greeting_patterns):
        intent = "greeting"
        confidence = 0.9
    
    # Fee-related queries (multilingual)
    elif any(pattern in text_lower for pattern in ["fee", "fees", "cost", "price", "amount", "charge", "tuition", 
                       "payment", "scholarship", "kitni fees", "fees kitni", "paisa", "rupee", 
                       "fees kya hai", "फीस", "शुल्क"]):
        intent = "fees"
        confidence = 0.8
    
    # Department queries (multilingual)
    elif any(pattern in text_lower for pattern in ["department", "branch", "course", "program", "engineering", 
                       "computer", "mechanical", "electrical", "civil", "it", "information technology",
                       "विभाग", "शाखा", "baare mein", "about", "ke baare mein"]):
        intent = "department"
        confidence = 0.9
        
        # Extract specific department
        dept_mapping = {
            'computer': ['computer', 'cs', 'cse', 'computer science', 'computer engineering'],
            'mechanical': ['mechanical', 'mech', 'mechanical engineering'],
            'electrical': ['electrical', 'ee', 'electrical engineering'],
            'civil': ['civil', 'civil engineering'],
            'it': ['it', 'information technology']
        }
        
        for dept, variations in dept_mapping.items():
            if any(variation in text_lower for variation in variations):
                entities['department'] = dept
                break
    
    # Admission queries (multilingual)
    elif any(pattern in text_lower for pattern in ["admission", "apply", "application", "entrance", "eligibility", 
                       "process", "procedure", "form", "admission kaise", "apply kaise", 
                       "प्रवेश", "दाखिला", "admission process"]):
        intent = "admission"
        confidence = 0.8
    
    # Faculty queries (multilingual)
    elif any(pattern in text_lower for pattern in ["faculty", "teacher", "professor", "staff", "hod", "head", 
                       "शिक्षक", "प्रोफेसर", "kaun hain", "faculty kaun"]):
        intent = "faculty"
        confidence = 0.8
    
    # Contact queries
    elif any(pattern in text_lower for pattern in ["contact", "phone", "email", "address", "location", 
                       "संपर्क", "पता", "contact kaise"]):
        intent = "contact"
        confidence = 0.8
    
    # Placement queries
    elif any(pattern in text_lower for pattern in ["placement", "job", "career", "company", "package", 
                       "salary", "नौकरी", "placement details"]):
        intent = "placement"
        confidence = 0.8
    
    return intent, entities, confidence

def generate_response(intent, entities, language, confidence):
    """Generate appropriate response based on intent, entities, and language"""
    
    # Select appropriate responses based on language
    if language == 'hindi' and 'hindi_responses' in college_data:
        responses = college_data['hindi_responses']
    elif language == 'hinglish' and 'hinglish_responses' in college_data:
        responses = college_data['hinglish_responses']
    elif 'english_responses' in college_data:
        responses = college_data['english_responses']
    else:
        # Fallback to basic responses
        responses = college_data.get('responses', {})
    
    try:
        if intent == 'greeting':
            return responses.get('greeting', "Hello! How can I help you with college information?")
        
        elif intent == 'fees':
            if isinstance(responses.get('fees'), dict):
                return responses['fees'].get('overview', "Fee information not available.")
            else:
                return responses.get('fees', "Fee information not available.")
        
        elif intent == 'admission':
            return responses.get('admission_info', responses.get('admission', "Admission information not available."))
        
        elif intent == 'department':
            if 'department' in entities:
                dept = entities['department']
                # Return detailed department info from the extensive department data
                if dept == 'computer':
                    return cse_engineering_info['about']
                elif dept == 'mechanical':
                    return mechanical_engineering_info['about']
                elif dept == 'electrical':
                    return electrical_engineering_info['about']
                elif dept == 'civil':
                    return civil_engineering_info['about']
                elif dept == 'it':
                    return it_engineering_info['about']
                else:
                    return responses.get('department_info', "Department information not available.")
            else:
                return responses.get('department_info', "We have Computer, Mechanical, Electrical, Civil, and IT departments.")
        
        elif intent == 'faculty':
            return responses.get('faculty', "Our faculty information is available for all departments.")
        
        elif intent == 'contact':
            return responses.get('contact_details', contact_info if 'contact_info' in globals() else "Contact information not available.")
        
        elif intent == 'placement':
            return responses.get('placement', "Our college has excellent placement opportunities with top companies.")
        
        else:
            # Default response
            return responses.get('default', "I'm here to help you with college information. Please ask about admissions, fees, departments, or facilities.")
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try asking in a different way."

# College information
college_name = "R.V. Parankar College of Engineering and Technology, Arvi"
departments = ["Computer Engineering", "Mechanical Engineering", 
               "Electrical Engineering", "Civil Engineering" ]
courses = {"B.Tech": "4 years"}
admission_dates = "June 1 - August 15, 2025  "
contact_info = "Phone: 0721-1234567 | Email:pcetarvi@rediffmail.com | www.rvparankar.in"

# Department button template
dept_buttons = """
<div class="button-container">
    <button class="dept-button" onclick="sendButtonMessage('about {dept} engineering')">About</button>
    <button class="dept-button" onclick="sendButtonMessage('vision of {dept} engineering')">Vision</button>
    <button class="dept-button" onclick="sendButtonMessage('mission of {dept} engineering')">Mission</button>
    <button class="dept-button" onclick="sendButtonMessage('labs in {dept} engineering')">Our Labs</button>

    <button class="dept-button" onclick="sendButtonMessage('programs in {dept}')">Programs</button>
    <button class="dept-button" onclick="sendButtonMessage('infrastructure in {dept}')">Infrastructure</button>
    <button class="dept-button" onclick="sendButtonMessage('faculty in {dept}')">Faculty</button>
    <button class="dept-button" onclick="sendButtonMessage('research in {dept}')">Research</button>
    <button class="dept-button" onclick="sendButtonMessage('activities in {dept}')">Activities</button>
     <button class="dept-button" onclick="sendButtonMessage('achievements in {dept}')">Achievements</button>

       <button class="info-button" onclick="sendButtonMessage('president')">President</button>
    <button class="info-button" onclick="sendButtonMessage('principal')">Principal</button>
    <button class="info-button" onclick="sendButtonMessage('director')">Director</button>
    <button class="info-button" onclick="sendButtonMessage('college address')">Address</button>
    <button class="info-button" onclick="sendButtonMessage('admission contact')">Admission</button>
    <button class="info-button" onclick="sendButtonMessage('college contact')">Contact</button>

    


   </div>
"""

leadership_info = {
    "president": """
    <strong>President</strong><br>
    Hon. Mr. G. W. Parankar<br>
    President
    """,
    "principal": """
    <strong>Principal</strong><br>
    Hon. Mrs. P.R. Parankar<br>
    Secretary
    """,
    "director": """
    <strong>Director</strong><br>
    Hon. Dr. R. W. Parankar<br>
    Director
    """,
    "address": """
    <strong>R.V. PARANKAR COLLEGE of Engineering & Technology, ARVI</strong><br>
    Survey no.116/18, Mauza Sarangpuri,<br>
    Arvi-Wardha NH-647, Arvi - 442201,<br>
    Dist-Wardha, Maharashtra
    """,
    "admission": """
    <strong>Admission Enquiry</strong><br>
    8857086610, 9890377246<br>
    9923255884, 8600443031
    """,
    "contact": """
    <strong>Contact Us</strong><br>
    www.rvparankar.in<br>
    pcetarvi@rediffmail.com<br>
    principalpcet1@gmail.com
    """
}


# Civil Engineering Department
civil_engineering_info = {
    "about": """
    <strong>DEPARTMENT OF CIVIL ENGINEERING</strong><br>
    R.V. Parankar College of Engineering And Technology<br><br>
    
    <strong>ABOUT US</strong><br>
    The R.V. Parankar College of Engineering And Technology offers Civil Engineering Department a full time Undergraduate programme in B.E. Civil Engineering.<br><br>
    
    The Department has a very able and skilled team of faculty members. The aim is to educate, train and develop highly skilled Civil Engineers at all levels capable of designing, constructing and maintaining environmental-friendly infrastructures.<br><br>
    
    The Civil Engineering laboratories are well equipped with latest instruments and machineries and cater to the Undergraduate students from Civil. The class room facilities are renowned for the academic and excellence.
    """,
    "vision": """
    <strong>VISION</strong><br>
    To create a high quality civil engineers with a technical knowledge of global standards to face the current and future challenges in the field. To guide a student for provide a good service to our nation with a sound knowledge.
    """,
    "mission": """
    <strong>MISSION</strong><br>
    To create professionals who are trained in the design and development of civil engineering systems and contribute towards research activities.<br>
    To provide consultancy services to the community in all areas of civil engineering.<br>
    To encourage students to study higher education and write competitive exams and various career developing courses.
    """,
    "labs": """
    <strong>LABORATORIES & FACILITIES</strong><br>
    - Concrete Technology Lab<br>
    - Geotechnical Engineering Lab<br>
    - Transportation Engineering Lab<br>
    - Environmental Engineering Lab<br>
    - Surveying Lab<br>
    - Hydraulics & Hydraulic Machines Lab<br>
    - CAD Lab with latest software
    """
}


# Mechanical Engineering Department
mechanical_engineering_info = {
    "about": """
    <strong>DEPARTMENT OF MECHANICAL ENGINEERING</strong><br>
    R.V. Parankar College of Engineering And Technology<br><br>
    
    <strong>ABOUT US</strong><br>
    The R.V. Parankar College of Engineering And Technology offers a full time Graduate Program in Mechanical Engineering that creates a community of top-notch scholars by bringing together faculty members which will establish graduate students with a common interest in innovation, creativity, and advanced professional study.<br><br>
    
    Through the curriculum, our department strives to prepare our undergraduate students for careers in traditional Mechanical Engineering fields as well as careers in cross-disciplined areas in academia and industry.<br><br>
    
    We pride ourselves on our faculty who guide each student from both exam and industry perspectives.<br><br>
    
    <strong>Specializations:</strong><br>
    - Thermal and Fluid Sciences<br>
    - Materials and Manufacturing<br>
    - Mechanics and Systems<br>
    - Controls<br><br>
    
    The best way to learn more about Mechanical Engineering at our institution is to visit us. We hope to see you soon!
    """,
    "vision": """
    <strong>VISION</strong><br>
    The Mechanical Engineering Department endeavors to be recognized globally for outstanding education and research leading to well qualified engineers, who are innovative, entrepreneurial and successful in advanced fields of mechanical engineering to cater the ever changing industrial demands and social needs.
    """,
    "mission": """
    <strong>MISSION</strong><br>
    The mission of the Department of Mechanical Engineering is to serve the students of our institution, the State, and the nation by:<br><br>
    
    - Providing quality education that is well-grounded in the fundamental principles of engineering, fostering innovation, and preparing students for leadership positions and successful careers in industry, government and academia.<br>
    - Advancing the knowledge base of mechanical engineering to support the competitiveness of existing industry and to spawn new economic development through active involvement in basic and applied research in a global context.<br>
    - Providing professional development opportunities for practicing engineers through continuing education, service, and outreach activities.
    """,
    "labs": """
    <strong>OUR LABS</strong><br>
    <strong>Fluid Machine Lab:</strong> Our state-of-the-art laboratory equipped with modern equipment for hands-on learning and research in fluid dynamics and machinery.
    """
}


# Electrical Engineering Department
electrical_engineering_info = {
    "about": """
    <strong>DEPARTMENT OF ELECTRICAL ENGINEERING</strong><br>
    R.V. Parankar College of Engineering And Technology<br><br>
    
    <strong>ABOUT US</strong><br>
    We have a graduate program in Electrical Engineering Department which is a brilliant rainbow of young minds from all over the country, with students coming from competitive pools and staff members who have good reputations for their work ethics.<br><br>
    
    The Department offers sound theoretical and practical training in state-of-the-art equipment. The Department is backed by good requirements of industries and establishments. The department offers B.E. course in Full time.
    """,
    "vision": """
    <strong>VISION</strong><br>
    Our vision is to produce Electrical Engineers with dynamic well-rounded personalities adaptable to ever increasing demands of emerging technologies involving analytical and practical skills.
    """,
    "mission": """
    <strong>MISSION</strong><br>
    - To offer good quality Under-Graduate, Post-Graduate and Doctoral programmes in electrical and electronics engineering<br>
    - To provide state-of-the-art resources that contribute to achieve excellence in teaching-learning, research and development activities<br>
    - To bridge the gap between industry and academia by framing curricula and syllabi based on industrial and societal needs<br>
    - To provide suitable forums to enhance the creative talents of students and faculty members<br>
    - To enable students to develop skills to solve complex technological problems of current times and also provide a framework for promoting collaborative and multidisciplinary activities<br>
    - To inculcate moral and ethical values among the faculty and students
    """,
    "labs": """
    <strong>OUR LABS</strong><br>
    <strong>Network Analysis Lab:</strong> Equipped with modern instruments for circuit analysis and network theorems<br><br>
    <strong>Electrical Machine Lab:</strong> Hands-on experience with generators, motors, and transformers
    """
}


# Information Technology Department
it_engineering_info = {
    "about": """
    <strong>DEPARTMENT OF INFORMATION TECHNOLOGY</strong><br>
    R.V. Parankar College of Engineering And Technology<br><br>
    
    <strong>ABOUT US</strong><br>
    Welcome to the Department of Information Technology. The Department is responsible for providing information and training in the world's everyday life of information technology. Our program combines information resources with practical applications to prepare students for successful careers in the IT industry.
    """,
    "vision": """
    <strong>VISION</strong><br>
    To be a premier center for Information Technology education, fostering innovative thinking and developing professionals who solve contemporary technology challenges.
    """,
    "mission": """
    <strong>MISSION</strong><br>
    - Impart comprehensive education in Technology fundamentals and applications<br>
    - Develop technical skills throughout the community and enhance student learning<br>
    - Develop professional development opportunities through educational design<br>
    - Optimize industry partnerships and social support during student development<br>
    - Promote practical and social opportunities in technology development
    """,
    "programs": """
    <strong>PROGRAMS OFFERED</strong><br><br>
    <strong>Ethics in Information Technology</strong><br>
    - ACCEL supported curriculum<br>
    - Focus on relevant developments in database management, networking, and IT infrastructure<br><br>
    
    <strong>Advanced Information Technology</strong><br>
    - Advanced study in emerging IT domains<br>
    - Research-focused approach<br><br>
    
    <strong>Automation Technology</strong><br>
    - Resource opportunities for research in IT specifications<br>
    - Industry-aligned curriculum
    """,
    "infrastructure": """
    <strong>INFRASTRUCTURE</strong><br>
    Our department provides modern facilities to support effective learning:<br><br>
    
    <strong>Computer Laboratories</strong><br>
    - Current hardware and software resources<br>
    - High-speed internet connectivity<br><br>
    
    <strong>Specialized Tools</strong><br>
    - Software testing tools<br>
    - Internet security systems<br>
    - Data intelligence platforms
    """,
    "faculty": """
    <strong>FACULTY</strong><br>
    The department is supported by qualified faculty members with diverse expertise in Information Technology disciplines. Our instructors combine academic knowledge with practical experience to provide students with well-rounded education.
    """,
    "research": """
    <strong>RESEARCH AREAS</strong><br><br>
    <strong>Core Technologies</strong><br>
    - Data Mining and Business Intelligence<br>
    - Network Systems and Architecture<br><br>
    
    <strong>Emerging Fields</strong><br>
    - Dynamic Software Interaction<br>
    - Machine Learning Applications
    """,
    "activities": """
    <strong>STUDENT ACTIVITIES</strong><br><br>
    <strong>Technical Development</strong><br>
    - IT project challenges<br>
    - Technical peer presentations<br><br>
    
    <strong>Professional Growth</strong><br>
    - Business development workshops<br>
    - Student experience enhancement programs
    """
}


# Computer Science Engineering Department
cse_engineering_info = {
    "about": """
    <strong>DEPARTMENT OF COMPUTER SCIENCE ENGINEERING</strong><br>
    R.V. Parankar College of Engineering And Technology<br><br>
    
    <strong>ABOUT US</strong><br>
    Welcome to the Department of Computer Science Engineering. We are committed to excellence in computing education, research, and innovation. Our program provides students with a strong foundation in computer science principles along with practical skills to solve complex computing problems.
    """,
    "vision": """
    <strong>VISION</strong><br>
    To be recognized as a center of excellence in Computer Science Education and Research, producing globally competent professionals who can contribute to technological advancements and societal development.
    """,
    "mission": """
    <strong>MISSION</strong><br>
    - Provide quality education in computer science fundamentals and emerging technologies<br>
    - Foster innovation through research and development activities<br>
    - Develop problem-solving skills through hands-on learning experiences<br>
    - Establish strong industry-academia collaborations<br>
    - Promote ethical values and social responsibility among students
    """,
    "programs": """
    <strong>PROGRAMS OFFERED</strong><br><br>
    <strong>Bachelor of Engineering (CSE)</strong><br>
    - 4-year undergraduate program<br>
    - Specializations in AI, Cybersecurity, and Data Science<br>
    - Industry-aligned curriculum<br><br>
    
    <strong>Master of Technology (CSE)</strong><br>
    - 2-year postgraduate program<br>
    - Research-focused with thesis option<br>
    - Advanced courses in emerging technologies<br><br>
    
    <strong>Doctoral Program (Ph.D.)</strong><br>
    - Research in cutting-edge computing areas<br>
    - Collaboration with industry and research labs<br>
    - Interdisciplinary research opportunities
    """,
    "labs": """
    <strong>LABORATORIES</strong><br>
    Our department boasts state-of-the-art computing facilities:<br><br>
    
    <strong>Advanced Computing Lab</strong><br>
    - High-performance workstations<br>
    - Cloud computing infrastructure<br>
    - Parallel computing resources<br><br>
    
    <strong>AI & Data Science Lab</strong><br>
    - GPU-accelerated systems<br>
    - Big data processing tools<br>
    - Machine learning frameworks<br><br>
    
    <strong>Networking & Cybersecurity Lab</strong><br>
    - Cisco networking equipment<br>
    - Ethical hacking tools<br>
    - Security testing environment
    """,
    "faculty": """
    <strong>FACULTY</strong><br>
    Our faculty members are highly qualified with expertise in various domains of computer science including Artificial Intelligence, Cybersecurity, Software Engineering, and Data Science. Many hold Ph.D. degrees and have extensive research and industry experience.
    """,
    "research": """
    <strong>RESEARCH AREAS</strong><br><br>
    <strong>Core Computing</strong><br>
    - Algorithms and Complexity<br>
    - Computer Systems and Architecture<br>
    - Programming Languages<br><br>
    
    <strong>Emerging Technologies</strong><br>
    - Artificial Intelligence and Machine Learning<br>
    - Internet of Things (IoT)<br>
    - Blockchain Technology<br><br>
    
    <strong>Applied Computing</strong><br>
    - Data Science and Big Data Analytics<br>
    - Computer Vision and Image Processing<br>
    - Cloud and Edge Computing
    """,
    "achievements": """
    <strong>STUDENT ACHIEVEMENTS</strong><br><br>
    <strong>Technical Competitions</strong><br>
    - Hackathon winners at national level<br>
    - Coding competition champions<br>
    - Research paper publications<br><br>
    
    <strong>Placements</strong><br>
    - 100+ placements in top tech companies<br>
    - Higher studies at prestigious universities<br>
    - Successful startup ventures
    """
}


discipline_rules = {
    "overview": """
    <strong>College Discipline & Rules</strong><br><br>
    The College is a community in which a large number of people live together. It is therefore essential that all members have due regard for the rights of others. The Incharge Principal/Faculty (Student Activities) looks after the disciplinary matters and problems arising from a breach of the College rules. The College rules are intended to help preserve a happy and harmonious atmosphere for all those living and working in the College.
    """,
    "attendance": """
    <strong>ATTENDANCE</strong><br><br>
    • Students should fulfill minimum 75% attendance for all programs (theory & practical)<br>
    • As per Nagpur University Ordinance No. 6<br>
    • Absences must be reported in writing in advance<br>
    • Students failing to meet attendance requirements won't be eligible for certification
    """,
    "ragging": """
    <strong>RAGGING</strong><br><br>
    • Strictly forbidden by law (Maharashtra Prohibition on Ragging Act 1999)<br>
    • Penalties include:<br>
      &nbsp;&nbsp;- Up to 2 years imprisonment<br>
      &nbsp;&nbsp;- Fine up to ₹10,000<br>
      &nbsp;&nbsp;- Dismissal from college for 5 years
    """,
    "anti_social": """
    <strong>ANTI-SOCIAL ACTIVITIES</strong><br><br>
    • Participation in political/anti-social activities prohibited<br>
    • Strict disciplinary action will be taken against violators
    """,
    "uniform": """
    <strong>UNIFORM</strong><br><br>
    • Prescribed dress code must be followed<br>
    • Aprons compulsory in laboratories<br>
    • No eatables in labs<br>
    • Mobile phones strictly prohibited in lab areas
    """,
    "library": """
    <strong>LIBRARY</strong><br><br>
    • Books arranged systematically by title/subject<br>
    • Students must maintain this order during reference work<br>
    • Mobile phones strictly prohibited
    """,
    "behavior": """
    <strong>BEHAVIOR</strong><br><br>
    • Students must conduct themselves appropriately at all times<br>
    • Must uphold the institution's image and standing
    """,
    "schedule": """
    <strong>TIME SCHEDULE</strong><br><br>
    • Students must arrive on time and attend all lectures<br>
    • All term work must be completed as scheduled<br>
    • Failure to complete term work may result in being barred from university exams
    """,
    "conduct": """
    <strong>CONDUCT</strong><br><br>
    • Students accountable for behavior both on and off campus<br>
    • Tampering with fire safety equipment is a serious offense
    """,
    "general": """
    <strong>GENERAL RULES</strong><br><br>
    • Must abide by all college rules and regulations<br>
    • Regularly check notice boards for updates<br>
    • Always carry ID card on campus<br>
    • Playing games on campus prohibited<br>
    • Severe punishments including rustication for misbehavior
    """
}



# Transportation Information
transportation_info = {
    "overview": """
    <strong>School Bus Transportation</strong><br><br>
    Our safe and reliable bus service connects major city locations to the college campus, ensuring convenient transportation for all students.
    """,
    "features": """
    <strong>Key Features</strong><br><br>
    • Comprehensive Coverage: Serving all major neighborhoods and city stops<br>
    • Multiple Routes: Options to suit different schedules<br>
    • Regular Timings: Morning and afternoon services<br>
    • Safety First: GPS-equipped buses with trained drivers<br>
    • Student ID Access: Easy boarding with college ID cards
    """,
    "schedule": """
    <strong>Schedule Information</strong><br><br>
    <strong>Morning Pickups:</strong> 9:00 AM - 10:30 AM (every 20-30 minutes)<br><br>
    <strong>Afternoon Returns:</strong> 5:00 PM - 6:30 PM<br><br>
    Special schedules available during exams and events
    """
}



# Workshop Information
workshop_info = {
    "overview": """
    <strong>General Workshop</strong><br><br>
    The General Workshop forms an integral part of the Institution as it is heavily involved in carrying out the practical oriented study of various manufacturing activities with the help of sophisticated equipment, machinery, and tools.<br><br>
    Basic Engineering workshop curriculum is framed in all engineering/technology programmes to make all students proficient in the use of hand tools, equipment and machinery in various workshop sections.
    """,
    "fitting": """
    <strong>Fitting Section</strong><br><br>
    In fitting shop various processes are performed on metals to give them desired shape and size and fit them with mating parts. Both ferrous and non-ferrous metals are dealt with in this section.
    """,
    "carpentry": """
    <strong>Carpentry Section</strong><br><br>
    Carpentry is a skilled trade in which the primary work performed is the use of wood to construct items as large as buildings and as small as desk drawers. Students learn wood-working skills like making furniture and wooden articles.
    """,
    "welding": """
    <strong>Welding Section</strong><br><br>
    A well maintained and advanced Welding section provides hands-on introduction to the common welding processes used in industry.
    """
}



# Computer Facilities Information
computer_info = {
    "overview": """
    <strong>Computer Facility</strong><br><br>
    Our state-of-the-art computer facilities provide students with access to cutting-edge technology and software to support their academic and research needs.
    """,
    "features": """
    <strong>High-Performance Labs</strong><br>
    • Multiple computer labs equipped with latest hardware<br>
    • High-speed internet connectivity<br><br>
    
    <strong>Specialized Software</strong><br>
    • Access to industry-standard software for engineering, design, programming, and data analysis<br><br>
    
    <strong>24/7 Access</strong><br>
    • Selected labs available round-the-clock for projects and assignments<br><br>
    
    <strong>Technical Support</strong><br>
    • Dedicated staff available to assist with technical issues
    """,
    "resources": """
    <strong>Available Resources</strong><br><br>
    • 300+ workstations across campus<br>
    • High-end workstations for CAD/CAM applications<br>
    • 3D printing and rapid prototyping facilities<br>
    • Virtual reality development lab<br>
    • Data center with cloud computing resources
    """
}



# Library Information
library_info = {
    "overview": """
    <strong>Convenient Library</strong><br><br>
    Our modern library provides students with comprehensive resources and a peaceful environment for study and research, supporting all academic programs.
    """,
    "services": """
    <strong>Library Services</strong><br><br>
    • 100,000+ print volumes<br>
    • Access to 50+ online databases<br>
    • 200+ print journal subscriptions<br>
    • E-book collection (50,000+ titles)<br>
    • Interlibrary loan services<br>
    • Reference assistance<br>
    • Study rooms and carrels<br>
    • Printing and scanning facilities<br>
    • Accessibility services<br>
    • Information literacy instruction
    """,
    "facilities": """
    <strong>Facilities</strong><br><br>
    <strong>Reading Areas</strong><br>
    • Comfortable seating with natural lighting<br><br>
    
    <strong>Digital Resources</strong><br>
    • Computer stations with online resource access<br><br>
    
    <strong>Group Study Rooms</strong><br>
    • Bookable rooms with presentation technology<br><br>
    
    <strong>Special Collections</strong><br>
    • Rare books and archives for specialized research
    """
}


# B.Tech Fees Structure Information
btech_fees = {
    "overview": """
    <strong>B.Tech Fee Structure (2024-25)</strong><br><br>
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Category</th>
            <th>Indian Students (₹)</th>
            <th>International Students ($)</th>
        </tr>
        <tr>
            <td>Tuition Fee</td>
            <td>1,20,000</td>
            <td>2,000</td>
        </tr>
        <tr>
            <td>Development Fee</td>
            <td>1,000</td>
            <td>500</td>
        </tr>
        <tr>
            <td>Examination Fee</td>
            <td>2,300</td>
            <td>-</td>
        </tr>
        <tr>
            <td>Other Charges</td>
            <td>8,000</td>
            <td>300</td>
        </tr>
        <tr>
            <td><strong>Total Annual Fees</strong></td>
            <td><strong>1,31,000</strong></td>
            <td><strong>2,800</strong></td>
        </tr>
    </table>
    """,
    "payment": """
    <strong>Payment Options for B.Tech</strong><br><br>
    • <strong>Installment Plan:</strong> 50% at admission + 50% before semester 2<br>
    • <strong>Payment Methods:</strong> Online/NEFT/DD/Cash<br>
    • <strong>Early Bird Discount:</strong> 5% on full annual payment<br>
    • <strong>Late Fee:</strong> ₹500/week after due date
    """,
    "scholarship": """
    <strong>B.Tech Scholarships</strong><br><br>
    • <strong>Merit Scholarship:</strong> Up to 50% fee waiver (Based on 12th/JEE score)<br>
    • <strong>EBC Scholarship:</strong> 25% waiver for economically backward students<br>
    • <strong>Sports Quota:</strong> 30-50% waiver for state/national players<br>
    • <strong>Girl Child Scholarship:</strong> 20% waiver for female students
    """
}


# Disability Friendly Facilities Information
disability_facilities = {
    "overview": """
    <strong>Disability Friendly Facilities</strong><br><br>
    Our college is committed to providing an inclusive environment for all students. We offer comprehensive support services and accessible facilities to ensure equal opportunities for students with disabilities.
    """,
    "support": """
    <strong>Support Services</strong><br><br>
    • Dedicated disability support coordinator<br>
    • Counseling services for students with disabilities<br>
    • Peer mentoring program<br>
    • Assistive technology training<br>
    • Regular accessibility audits of campus facilities
    """,
    "accessibility": """
    <strong>Physical Accessibility</strong><br><br>
    • Wheelchair ramps at all building entrances<br>
    • Elevators with Braille buttons and audio announcements<br>
    • Disabled-friendly restrooms on each floor<br>
    • Tactile pathways for visually impaired students<br>
    • Accessible seating in classrooms and auditoriums
    """,
    "learning": """
    <strong>Learning Support</strong><br><br>
    • Specialized software for students with learning disabilities<br>
    • Screen readers and magnifiers available in computer labs<br>
    • Sign language interpreters available upon request<br>
    • Extended time for exams when needed<br>
    • Alternative format textbooks (audio, braille, large print)
    """,
    "campus": """
    <strong>Campus Facilities</strong><br><br>
    • Reserved parking spaces near all buildings<br>
    • Accessible cafeteria with adjustable furniture<br>
    • Disabled-friendly hostel accommodations<br>
    • Emergency alert systems with visual and audio signals<br>
    • Accessible sports and recreation facilities
    """,
    "contact": """
    <strong>Need Disability Support?</strong><br><br>
    Our dedicated support team is available to assist students with disabilities. Contact us for personalized assistance and accommodations.
    """
}

# Faculty Information by Department
faculty_data = {
    "civil": [
        {
            "name": "Prof.Dr.Ravindra W.Parankar",
            "position": "Head of Department",
            "education": "PHD, M.Tech, MA, DCE",
            "experience": "21 Years",
            "contact": "7620245615",
            "email": ""
        },
        {
            "name": "Prof.Rahul M Kachole",
            "position": "Associate Professor",
            "education": "M.Tech",
            "experience": "18 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Pranav P.Pande",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "11 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Mohit Chandak",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "10 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Jayesh Gandhi",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "05 Years",
            "contact": "",
            "email": ""
        }
    ],
    "mechanical": [
        {
            "name": "Prof. Nikhil Ekotkhane",
            "position": "H.O.D. (Mechanical Engineering)",
            "education": "M.Tech (Machine Design)",
            "experience": "12 Years",
            "contact": "9890377246",
            "email": ""
        },
        {
            "name": "Dr. Krishnan",
            "position": "Associate Professor",
            "education": "M.Tech, PhD",
            "experience": "10 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof. Yogesh A. Paliwal",
            "position": "Assistant Professor",
            "education": "M.Tech, BE, DME (Thermal Engineering)",
            "experience": "20 Years",
            "contact": "9923255884",
            "email": "Email Professor"
        },
        {
            "name": "Prof. Pravin A. Sapane",
            "position": "Assistant Professor",
            "education": "M.Tech, BE, DME (Advance Production Tech.)",
            "experience": "17 Years",
            "contact": "8857086610",
            "email": "Email Professor"
        },
        {
            "name": "Prof. Tarachand G. Lokhande",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "15 Years",
            "contact": "",
            "email": ""
        }
    ],
    "electrical": [
        {
            "name": "Prof.Dr.E.Sujata",
            "position": "H.O.D. (Electrical Engineering)",
            "education": "Ph.D, M.Tech",
            "experience": "15+ Years in Teaching & Research",
            "contact": "+91 9999377246",
            "email": "Contact Professor"
        },
        {
            "name": "Prof.Mehendra A. Gurunasingani",
            "position": "Associate Professor",
            "education": "M.Tech, BE",
            "experience": "12 Years Teaching Experience",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Harsha V.Hood",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "10 Years in Teaching",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Sanket Thakare",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "2 Years Teaching Experience",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Vaishnavi Bhende",
            "position": "Assistant Professor",
            "education": "Ph.D, M.Tech, BE",
            "experience": "10 Years in Teaching & Research",
            "contact": "",
            "email": "Email Professor"
        }
    ],


    
 "computer": [
        {
            "name": "Prof.Priti D.Ghantewar",
            "position": "H.O.D. (Computer Science & Engineering)",
            "education": "Ph.D(A), M.Tech",
            "experience": "16 Years",
            "contact": "8669022917",
            "email": "Contact HOD"
        },
        {
            "name": "Dr.K.Muralibabu",
            "position": "Associate Professor",
            "education": "Ph.D, M.Tech",
            "experience": "12 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Manisha B.Bannagare",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "10 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Rutuja A.Khodake",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "05 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Nitin M.Wadnare",
            "position": "Assistant Professor",
            "education": "MSc(Computer)",
            "experience": "08 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Swati P.Akhare",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "06 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Amol Sarode",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "15 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Deepali Gajanan Hande",
            "position": "Assistant Professor",
            "education": "M.Tech(AI)",
            "experience": "04 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Snehal V.Borade",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "04 Years",
            "contact": "",
            "email": "Email Professor"
        }
    ],


     "it": [
        {
            "name": "Prof.Priti D.Ghantewar",
            "position": "H.O.D. (Information Technology)",
            "education": "Ph.D(A), M.Tech",
            "experience": "16 Years",
            "contact": "8669022917",
            "email": "Contact HOD"
        },
        {
            "name": "Dr.K.Muralibabu",
            "position": "Associate Professor",
            "education": "Ph.D, M.Tech",
            "experience": "12 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Manisha B.Bannagare",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "10 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Rutuja A.Khodake",
            "position": "Assistant Professor",
            "education": "M.Tech, BE",
            "experience": "05 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Nitin M.Wadnare",
            "position": "Assistant Professor",
            "education": "MSc(Computer)",
            "experience": "08 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Swati P.Akhare",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "06 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Amol Sarode",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "15 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Deepali Gajanan Hande",
            "position": "Assistant Professor",
            "education": "M.Tech(AI)",
            "experience": "04 Years",
            "contact": "",
            "email": "Email Professor"
        },
        {
            "name": "Prof.Snehal V.Borade",
            "position": "Assistant Professor",
            "education": "M.Tech",
            "experience": "04 Years",
            "contact": "",
            "email": "Email Professor"
        }
    ]
}



responses = {
    "greeting": [
        "Welcome to R.V. Parankar College B.Tech Admission Helpdesk!",
        "Hello! How can I assist you with B.Tech admissions today?",
        "Hi there! Ask me about B.Tech fee structure or admission process."
    ],
    "fees": {
        "main": btech_fees["overview"],
        "payment": btech_fees["payment"],
        "scholarship": btech_fees["scholarship"],
        "default": btech_fees["overview"] + "<br><br>You can also ask about:<br>- Payment options<br>- Scholarship opportunities"
    },
    "default": "I can provide information about B.Tech fees. Try asking:<br>- What is the B.Tech fee structure?<br>- What are the payment options?<br>- Are there any scholarships available?"
}


# Detailed responses for each category
department_info = """
<strong>Departments Offered:</strong><br><br>
1. <strong>Computer Engineering</strong><br>
   - Focus on software development and computer systems<br>
   - Well-equipped computer labs with latest technology<br><br>

2. <strong>Mechanical Engineering</strong><br>
   - Covers thermodynamics, fluid mechanics, and machine design<br>
   - State-of-the-art workshop facilities<br><br>

3. <strong>Electrical Engineering</strong><br>
   - Specializations in power systems and control systems<br>
   - Modern electrical machines and power electronics labs<br><br>

4. <strong>Civil Engineering</strong><br>
   - Focus on structural design and construction technology<br>
   - Comprehensive surveying and concrete technology labs
"""

courses_info = """
<strong>Courses Offered:</strong><br><br>
• <strong>Bachelor of Technology (B.Tech)</strong><br>
  - Duration: 4 years<br>
  - Specializations: Computer, Mechanical, Electrical, Civil<br><br>

• <strong>Diploma Programs</strong><br>
  - Duration: 3 years<br>
  - Available in all engineering disciplines<br><br>

• <strong>Post Graduate Programs</strong><br>
  - M.Tech in various specializations (2 years)
"""

admission_info = """
<strong>Admission Dates & Process:</strong><br><br>
• <strong>Application Period:</strong> June 1 - August 15, 2025<br>
• <strong>Eligibility:</strong> 10+2 with Physics, Chemistry, and Mathematics<br>
• <strong>Entrance Exam:</strong> JEE Main or State CET scores accepted<br><br>

<strong>Important Dates:</strong><br>
- Application Start: June 1, 2025<br>
- Last Date to Apply: August 15, 2025<br>
- Counseling Starts: August 20, 2025<br>
- Classes Begin: September 1, 2025
"""

contact_details = """
<strong>Contact Information:</strong><br><br>
• <strong>Address:</strong><br>
  R.V. Parankar College of Engineering & Technology,<br>
  Survey no.116/18, Mauza Sarangpuri,<br>
  Arvi-Wardha NH-647, Arvi - 442201,<br>
  Dist-Wardha, Maharashtra<br><br>

• <strong>Phone:</strong> 0721-1234567<br>
• <strong>Email:</strong> pcetarvi@rediffmail.com<br>
• <strong>Website:</strong> www.rvparankar.in<br><br>

<strong>Admission Helpline:</strong><br>
8857086610, 9890377246<br>
9923255884, 8600443031
"""




def get_department_response(dept, query_type):
    """Helper function to get department specific responses"""
    dept_map = {
        "civil": civil_engineering_info,
        "mechanical": mechanical_engineering_info,
        "electrical": electrical_engineering_info,
        "information technology": it_engineering_info,
        "it": it_engineering_info,
         "computer science": cse_engineering_info,
        "cse": cse_engineering_info,
        "computer science engineering": cse_engineering_info
    }
    dept_info = dept_map.get(dept, {})
    response = dept_info.get(query_type, "")
    buttons = dept_buttons.format(dept=dept)
    return response + buttons


def format_faculty_card(prof):
    """Format a faculty member's information as an HTML card."""
    return f"""
    <div class="faculty-card">
        <h3>{prof.get('name', '')}</h3>
        <p><strong>Position:</strong> {prof.get('position', '')}</p>
        <p><strong>Education:</strong> {prof.get('education', '')}</p>
        <p><strong>Experience:</strong> {prof.get('experience', '')}</p>
        {'<p><strong>Contact:</strong> ' + prof['contact'] + '</p>' if prof.get('contact') else ''}
        {'<p><strong>Email:</strong> ' + prof['email'] + '</p>' if prof.get('email') else ''}
    </div>
    """

def format_faculty_card(prof):
    """Format a faculty member's information as an HTML card."""
    contact_html = f'<p><strong>Contact:</strong> <a href="tel:{prof["contact"].replace(" ", "").replace("+", "")}">{prof["contact"]}</a></p>' if prof.get("contact") else ""
    email_html = f'<p><strong>Email:</strong> <a href="mailto:{prof["email"].split()[-1].lower()}@rvparankar.in">{prof["email"]}</a></p>' if prof.get("email") and "Email" in prof["email"] else f'<p>{prof.get("email", "")}</p>'
    
    return f"""
    <div class="faculty-card">
        <h3>{prof.get('name', '')}</h3>
        <p><strong>Position:</strong> {prof.get('position', '')}</p>
        <p><strong>Education:</strong> {prof.get('education', '')}</p>
        <p><strong>Experience:</strong> {prof.get('experience', '')}</p>
        {contact_html}
        {email_html}
    </div>
    """


def get_faculty_response(dept):
    icons = {
        "civil": "fas fa-hard-hat",
        "mechanical": "fas fa-cogs",
        "electrical": "fas fa-bolt",
        "computer": "fas fa-laptop-code",
        "it": "fas fa-network-wired"
    }
    dept_titles = {
        "civil": "Civil Engineering Faculty",
        "mechanical": "Mechanical Engineering Faculty",
        "electrical": "Electrical Engineering Faculty",
        "computer": "Computer Science Faculty",
        "it": "Information Technology Faculty"
    }
    icon = icons.get(dept, "fas fa-chalkboard-teacher")
    title = dept_titles.get(dept, "Faculty")
    cards = "".join([format_faculty_card(prof) for prof in faculty_data.get(dept, [])])
    
    if cards:
        return f"""
        <div class="faculty-section">
            <h2><i class="{icon}"></i> {title}</h2>
            <div class="faculty-grid">
                {cards}
            </div>
        </div>
        """
    else:
        return f"""
        <div class="faculty-section">
            <h2><i class="{icon}"></i> {title}</h2>
            <p>No faculty data available for this department.</p>
        </div>
        """

dept_buttons = """
<div class="dept-button-container">
    <button class="dept-button" onclick="sendButtonMessage('civil faculty')">Civil</button>
    <button class="dept-button" onclick="sendButtonMessage('mechanical faculty')">Mechanical</button>
    <button class="dept-button" onclick="sendButtonMessage('electrical faculty')">Electrical</button>
    <button class="dept-button" onclick="sendButtonMessage('computer faculty')">Computer</button>
    <button class="dept-button" onclick="sendButtonMessage('it faculty')">IT</button>
</div>
"""

# Faculty Card Formatting Function
def format_faculty_card(prof):
    """Format a faculty member's information as an HTML card."""
    contact_html = f'<p><strong>Contact:</strong> <a href="tel:{prof["contact"].replace(" ", "").replace("+", "")}">{prof["contact"]}</a></p>' if prof.get("contact") else ""
    email_html = f'<p><strong>Email:</strong> <a href="mailto:{prof["email"].split()[-1].lower()}@rvparankar.in">{prof["email"]}</a></p>' if prof.get("email") and "Email" in prof["email"] else f'<p>{prof.get("email", "")}</p>'
    
    return f"""
    <div class="faculty-card">
        <h3>{prof.get('name', '')}</h3>
        <p><strong>Position:</strong> {prof.get('position', '')}</p>
        <p><strong>Education:</strong> {prof.get('education', '')}</p>
        <p><strong>Experience:</strong> {prof.get('experience', '')}</p>
        {contact_html}
        {email_html}
    </div>
    """

# Function to get IT Faculty Response
def get_it_faculty_response():
    cards = "".join([format_faculty_card(prof) for prof in faculty_data.get("it", [])])
    return f"""
    <div class="faculty-section">
        <h2><i class="fas fa-network-wired"></i> Information Technology Faculty</h2>
        <div class="faculty-grid">
            {cards}
        </div>
    </div>
    """




# Sample responses for the chatbot
responses ={
    "greeting": [
        f"Welcome to {college_name}! How can I assist you with your admission queries today?",
        f"Hello! Thank you for considering {college_name}. What would you like to know?",
        f"Hi there! I'm here to help with admission information for {college_name}."
    ],

    "faculty": {
        "civil": lambda: get_faculty_response("civil") + dept_buttons,
        "mechanical": lambda: get_faculty_response("mechanical") + dept_buttons,
        "electrical": lambda: get_faculty_response("electrical") + dept_buttons,
        "computer": lambda: get_faculty_response("computer") + dept_buttons,
        "it": lambda: get_faculty_response("it") + dept_buttons,
        "default": lambda: f"""
        <div class="faculty-intro">
            <h2><i class="fas fa-chalkboard-teacher"></i> Our Distinguished Faculty</h2>
            <p>Select a department to view faculty members:</p>
            {dept_buttons}
        </div>
        """
    },
     # [Previous response templates remain unchanged...]
   
    "leadership": {
        "president": leadership_info["president"] + dept_buttons ,
        "principal": leadership_info["principal"] + dept_buttons ,
        "director": leadership_info["director"] + dept_buttons ,
        "address": leadership_info["address"] + dept_buttons ,
        "admission": leadership_info["admission"] + dept_buttons ,
        "contact": leadership_info["contact"] + dept_buttons ,
        "default": "Here's information about our institution:" + dept_buttons 
    },
   
   "discipline": {
        "full": "<br>".join(discipline_rules.values()),
        "attendance": discipline_rules["overview"] + "<br><br>" + discipline_rules["attendance"],
        "ragging": discipline_rules["overview"] + "<br><br>" + discipline_rules["ragging"],
        "anti_social": discipline_rules["overview"] + "<br><br>" + discipline_rules["anti_social"],
        "uniform": discipline_rules["overview"] + "<br><br>" + discipline_rules["uniform"],
        "library": discipline_rules["overview"] + "<br><br>" + discipline_rules["library"],
        "behavior": discipline_rules["overview"] + "<br><br>" + discipline_rules["behavior"],
        "schedule": discipline_rules["overview"] + "<br><br>" + discipline_rules["schedule"],
        "conduct": discipline_rules["overview"] + "<br><br>" + discipline_rules["conduct"],
        "general": discipline_rules["overview"] + "<br><br>" + discipline_rules["general"],
        "default": discipline_rules["overview"] + "<br><br>Please ask about specific rules like attendance, ragging, uniform, etc."
    },
    
   "transportation": {
        "overview": transportation_info["overview"],
        "features": transportation_info["features"],
        "schedule": transportation_info["schedule"],
        "default": transportation_info["overview"] + "<br><br>You can ask about bus features or schedules."
    },
   
   "workshop": {
        "overview": workshop_info["overview"],
        "fitting": workshop_info["fitting"],
        "carpentry": workshop_info["carpentry"],
        "welding": workshop_info["welding"],
        "default": workshop_info["overview"] + "<br><br>Ask about specific sections: fitting, carpentry, or welding."
    },
   
    "computer": {
        "overview": computer_info["overview"],
        "features": computer_info["features"],
        "resources": computer_info["resources"],
        "default": computer_info["overview"] + "<br><br>You can ask about lab features or available resources."
    },
   
    "library": {
        "overview": library_info["overview"],
        "services": library_info["services"],
        "facilities": library_info["facilities"],
        "default": library_info["overview"] + "<br><br>Ask about library services or facilities."
    },

    "fees": {
        "main": btech_fees["overview"],
        "payment": btech_fees["payment"],
        "scholarship": btech_fees["scholarship"],
        "default": btech_fees["overview"] + "<br><br>You can also ask about:<br>- Payment options<br>- Scholarship opportunities"
    },

     # [Previous response templates remain unchanged...]
   
    "disability": {
        "overview": disability_facilities["overview"],
        "support": disability_facilities["support"],
        "access": disability_facilities["accessibility"],
        "learning": disability_facilities["learning"],
        "campus": disability_facilities["campus"],
        "contact": disability_facilities["contact"],
        "default": disability_facilities["overview"] + "<br><br>You can ask about:<br>• Support services<br>• Physical accessibility<br>• Learning support<br>• Campus facilities<br>• How to contact support"
    }

}

# Hinglish responses
hinglish_responses = {
    "greeting": [
        f"Namaste! {college_name} me aapka swagat hai! Main aapki admission me kaise sahayta kar sakta hoon?",
        f"Hello! {college_name} me خوش آمدید. Aap kya janna chahte hain?",
        f"Hi! Main {college_name} ke admission process me aapki madad karne ke liye yahan hoon."
    ],
    "departments": department_info,
    "courses": courses_info,
    "admission": admission_info,
    "contact": contact_details,
    "faculty": {
        "civil": lambda: get_faculty_response("civil") + dept_buttons,
        "mechanical": lambda: get_faculty_response("mechanical") + dept_buttons,
        "electrical": lambda: get_faculty_response("electrical") + dept_buttons,
        "computer": lambda: get_faculty_response("computer") + dept_buttons,
        "it": lambda: get_faculty_response("it") + dept_buttons,
        "default": lambda: f"""
        <div class="faculty-intro">
            <h2><i class="fas fa-chalkboard-teacher"></i> Hamaare Pratishthit Faculty</h2>
            <p>Faculty sadasyon ko dekhne ke liye ek department chunein:</p>
            {dept_buttons}
        </div>
        """
    },
    "default": "Maaf kijiye, main samajh nahi paya. Kya aap departments, courses, admission dates, ya contact information ke baare me pooch sakte hain?"
}

# Hinglish detection keywords
hinglish_keywords = [
    'kya', 'kaise', 'kab', 'kaha', 'kyu', 'aap', 'tum', 'hai', 'hain', 'fee', 
    'admission', 'college', 'ka', 'ki', 'ke', 'mein', 'par', 'aur', 'batao', 
    'chahiye', 'mil', 'sakte', 'sakta', 'jaankari', 'prakriya', 'tareekh'
]

def is_hinglish(text):
    """Check if the text contains Hinglish keywords."""
    return any(keyword in text.lower().split() for keyword in hinglish_keywords)



@app.route('/')
def home():
    """Render the main chatbot interface"""
    return render_template('help.html', college_name=college_name)

@app.route('/get_response', methods=['POST'])
def get_response():
    """Handle user messages and return chatbot responses using NLP"""
    try:
        user_message = request.form['user_message'].strip()
        
        if not user_message:
            return jsonify({'response': "Please enter a message!"})
        
        # Process the message through our NLP pipeline
        language = get_language(user_message)
        intent, entities, confidence = get_intent_and_entities(user_message, language)
        response = generate_response(intent, entities, language, confidence)
        
        return jsonify({
            'response': response,
            'language': language,
            'intent': intent,
            'confidence': confidence
        })
        
    except Exception as e:
        print(f"Error in get_response: {e}")
        # Fallback to original logic if NLP fails
        user_message = request.form['user_message'].lower()
        
        use_hinglish = is_hinglish(user_message)
        current_responses = hinglish_responses if use_hinglish else responses
 
    # Determine the appropriate response
    if any(word in user_message for word in ['hi', 'hello', 'hey', 'namaste']):
        response = random.choice(current_responses["greeting"])
    elif 'department' in user_message or 'branch' in user_message:
        response = current_responses["departments"]
    elif 'course' in user_message or 'program' in user_message:
        response = current_responses["courses"]
    elif 'date' in user_message or 'when' in user_message or 'admission' in user_message:
        response = current_responses["admission"]
    elif 'contact' in user_message or 'phone' in user_message or 'email' in user_message:
        response = current_responses["contact"]
    elif 'faculty' in user_message or 'professor' in user_message or 'teacher' in user_message:
        if 'civil' in user_message:
            response = current_responses["faculty"]["civil"]()
        elif 'mechanical' in user_message:
            response = current_responses["faculty"]["mechanical"]()
        elif 'electrical' in user_message:
            response = current_responses["faculty"]["electrical"]()
        elif 'computer' in user_message or 'cse' in user_message:
            response = current_responses["faculty"]["computer"]()
        elif 'information technology' in user_message or 'it' in user_message:
            response = current_responses["faculty"]["it"]()
        else:
            response = current_responses["faculty"]["default"]()
    elif 'president' in user_message:
        response = responses["leadership"]["president"]
    elif 'principal' in user_message:
        response = responses["leadership"]["principal"]
    elif 'director' in user_message:
        response = responses["leadership"]["director"]
    elif 'address' in user_message:
        response = responses["leadership"]["address"]
    elif 'admission' in user_message and ('contact' in user_message or 'number' in user_message):
        response = responses["leadership"]["admission"]
    elif 'contact' in user_message and ('college' in user_message or 'email' in user_message):
        response = responses["leadership"]["contact"]
    elif 'college' in user_message and ('about' in user_message or 'info' in user_message):
        response = responses["leadership"]["default"]
    elif 'discipline' in user_message or 'rules' in user_message or 'regulation' in user_message:
        if 'attend' in user_message:
            response = responses["discipline"]["attendance"]
        elif 'ragg' in user_message:
            response = responses["discipline"]["ragging"]
        elif 'anti' in user_message or 'social' in user_message:
            response = responses["discipline"]["anti_social"]
        elif 'uniform' in user_message or 'dress' in user_message:
            response = responses["discipline"]["uniform"]
        elif 'library' in user_message:
            response = responses["discipline"]["library"]
        elif 'behav' in user_message:
            response = responses["discipline"]["behavior"]
        elif 'schedule' in user_message or 'time' in user_message:
            response = responses["discipline"]["schedule"]
        elif 'conduct' in user_message:
            response = responses["discipline"]["conduct"]
        elif 'general' in user_message or 'code' in user_message:
            response = responses["discipline"]["general"]
        elif 'all' in user_message or 'complete' in user_message:
            response = responses["discipline"]["full"]
        else:
            response = responses["discipline"]["default"]
    elif 'transport' in user_message or 'bus' in user_message:
        if 'feature' in user_message:
            response = responses["transportation"]["features"]
        elif 'schedule' in user_message or 'time' in user_message:
            response = responses["transportation"]["schedule"]
        else:
            response = responses["transportation"]["default"]
    elif 'workshop' in user_message:
        if 'fitting' in user_message:
            response = responses["workshop"]["fitting"]
        elif 'carpent' in user_message:
            response = responses["workshop"]["carpentry"]
        elif 'weld' in user_message:
            response = responses["workshop"]["welding"]
        else:
            response = responses["workshop"]["default"]
    elif 'computer' in user_message or 'lab' in user_message:
        if 'feature' in user_message:
            response = responses["computer"]["features"]
        elif 'resource' in user_message:
            response = responses["computer"]["resources"]
        else:
            response = responses["computer"]["default"]
    elif 'library' in user_message:
        if 'service' in user_message:
            response = responses["library"]["services"]
        elif 'facilit' in user_message:
            response = responses["library"]["facilities"]
        else:
            response = responses["library"]["default"]
    elif 'fee' in user_message or 'payment' in user_message or 'scholarship' in user_message:
        if 'payment' in user_message or 'pay' in user_message:
            response = responses["fees"]["payment"]
        elif 'scholarship' in user_message:
            response = responses["fees"]["scholarship"]
        else:
            response = responses["fees"]["main"]
    elif 'disab' in user_message or 'accessib' in user_message or 'special need' in user_message:
        if 'support' in user_message or 'service' in user_message:
            response = responses["disability"]["support"]
        elif 'physical' in user_message or 'ramp' in user_message or 'wheelchair' in user_message:
            response = responses["disability"]["access"]
        elif 'learn' in user_message or 'exam' in user_message or 'software' in user_message:
            response = responses["disability"]["learning"]
        elif 'campus' in user_message or 'hostel' in user_message or 'parking' in user_message:
            response = responses["disability"]["campus"]
        elif 'contact' in user_message or 'help' in user_message or 'assist' in user_message:
            response = responses["disability"]["contact"]
        else:
            response = responses["disability"]["default"]    
    else:
        response = current_responses["default"]
 
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)