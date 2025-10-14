#!/usr/bin/env python3
"""
Simple test for Gemini API integration
"""
import asyncio
import os

# Set the API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyCf8PZ4jxCYXHM4cTq8U4nAzKMFfCvTbIo'

try:
    import google.generativeai as genai
    
    async def test_gemini_basic():
        """Test basic Gemini functionality"""
        print("🚀 Testing Gemini AI Integration")
        print("=" * 50)
        
        # Configure Gemini
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test prompt
        test_prompt = """
        Analyze this government project document excerpt:
        
        PROJECT: Construction of 2-Lane Road in Tawang District
        LOCATION: Tawang, Arunachal Pradesh
        COST: Rs. 250 Crores
        DURATION: 36 months
        
        Please provide:
        1. Executive summary
        2. Key project details
        3. Language detected (English/Hindi/Assamese)
        """
        
        try:
            print("🔄 Sending request to Gemini...")
            response = await asyncio.to_thread(
                model.generate_content,
                test_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            
            print("✅ SUCCESS - Gemini API Response:")
            print("-" * 50)
            print(response.text)
            print("-" * 50)
            print("🎉 Gemini integration working!")
            
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            
    if __name__ == "__main__":
        asyncio.run(test_gemini_basic())
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please install: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {e}")