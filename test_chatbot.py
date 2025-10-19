#!/usr/bin/env python3
# Test script for the enhanced multilingual chatbot

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import functions directly from help2.py
from help2 import get_language, get_intent_and_entities, generate_response

def test_chatbot_responses():
    """Test various inputs to see what responses are generated"""
    
    test_queries = [
        "Hello",
        "Fees kya hai?", 
        "Computer engineering ke baare mein batao",
        "Admission process kya hai?",
        "Faculty kaun hain?",
        "Placement details",
        "Contact information",
        "Civil department about",
        "Mechanical engineering vision"
    ]
    
    print("🤖 Testing Enhanced Multilingual College Chatbot")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            # Test the NLP pipeline
            language = get_language(query)
            intent, entities, confidence = get_intent_and_entities(query, language)
            response = generate_response(intent, entities, language, confidence)
            
            print(f"🌐 Language: {language}")
            print(f"🎯 Intent: {intent}")
            print(f"📊 Confidence: {confidence}")
            print(f"🏷️ Entities: {entities}")
            print(f"💬 Response: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)

if __name__ == "__main__":
    test_chatbot_responses()
