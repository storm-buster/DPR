#!/usr/bin/env python3
"""
Test to list available Gemini models
"""
import os
import google.generativeai as genai

# Set the API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyCf8PZ4jxCYXHM4cTq8U4nAzKMFfCvTbIo'

try:
    print("🚀 Checking Available Gemini Models")
    print("=" * 50)
    
    # Configure Gemini
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    
    # List available models
    print("Available models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
            
except Exception as e:
    print(f"❌ Error: {e}")