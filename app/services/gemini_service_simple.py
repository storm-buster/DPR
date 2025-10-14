"""
Simplified Gemini AI Service without heavy RAG dependencies
Supports multilingual analysis (English, Hindi, Assamese)
"""
import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
import PyPDF2
from io import BytesIO

from ..core.config import settings


class SimpleGeminiService:
    """Simplified AI service using Gemini for document analysis"""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Language detection patterns
        self.language_patterns = {
            'hindi': re.compile(r'[\u0900-\u097F]+'),
            'assamese': re.compile(r'[\u0980-\u09FF]+'),
            'english': re.compile(r'[a-zA-Z]+')
        }
        
        # Multilingual prompts
        self.prompts = {
            'english': {
                'analysis': """Analyze this government project document and provide a comprehensive summary.
                
Document Content:
{content}

Please provide a structured analysis with:
1. Executive Summary (2-3 paragraphs)
2. Key Project Details (name, location, cost, duration, agency)
3. Technical Specifications
4. Financial Breakdown
5. Timeline and Phases
6. Risk Assessment
7. Expected Benefits
8. Compliance Status

Format the response as clear sections with bullet points.""",
                
                'validation': """Review this government project document for completeness and compliance.
                
Document Content:
{content}

Check for:
1. Mandatory sections presence
2. Financial details completeness
3. Technical specifications adequacy
4. Environmental clearances
5. Timeline feasibility
6. Risk mitigation measures

Provide a completeness score (0-100) and list missing or inadequate sections."""
            },
            
            'hindi': {
                'analysis': """इस सरकारी परियोजना दस्तावेज़ का विश्लेषण करें और एक व्यापक सारांश प्रदान करें।

दस्तावेज़ सामग्री:
{content}

कृपया संरचित विश्लेषण प्रदान करें:
1. कार्यकारी सारांश (2-3 पैराग्राफ)
2. मुख्य परियोजना विवरण (नाम, स्थान, लागत, अवधि, एजेंसी)
3. तकनीकी विनिर्देश
4. वित्तीय विवरण
5. समयसीमा और चरण
6. जोखिम मूल्यांकन
7. अपेक्षित लाभ
8. अनुपालन स्थिति

स्पष्ट अनुभागों के साथ प्रतिक्रिया को प्रारूपित करें।""",
                
                'validation': """पूर्णता और अनुपालन के लिए इस सरकारी परियोजना दस्तावेज़ की समीक्षा करें।

दस्तावेज़ सामग्री:
{content}

जांचें:
1. अनिवार्य अनुभागों की उपस्थिति
2. वित्तीय विवरण की पूर्णता
3. तकनीकी विनिर्देशों की पर्याप्तता
4. पर्यावरणीय मंजूरी
5. समयसीमा की व्यवहार्यता
6. जोखिम शमन उपाय

पूर्णता स्कोर (0-100) प्रदान करें और गुम या अपर्याप्त अनुभागों की सूची बनाएं।"""
            },
            
            'assamese': {
                'analysis': """এই চৰকাৰী প্ৰকল্পৰ নথিপত্ৰৰ বিশ্লেষণ কৰক আৰু এক বিস্তৃত সাৰাংশ প্ৰদান কৰক।

নথিপত্ৰৰ বিষয়বস্তু:
{content}

অনুগ্ৰহ কৰি গঠনমূলক বিশ্লেষণ প্ৰদান কৰক:
1. কাৰ্যকৰী সাৰাংশ (2-3 অনুচ্ছেদ)
2. মুখ্য প্ৰকল্পৰ বিৱৰণ (নাম, স্থান, খৰচ, সময়কাল, সংস্থা)
3. কাৰিকৰী নিৰ্দেশনা
4. আৰ্থিক বিভাজন
5. সময়সূচী আৰু পৰ্যায়
6. বিপদৰ মূল্যায়ন
7. প্ৰত্যাশিত সুবিধা
8. সম্মতিৰ অৱস্থা

স্পষ্ট বিভাগৰ সৈতে প্ৰতিক্ৰিয়া বিন্যাস কৰক।""",
                
                'validation': """সম্পূৰ্ণতা আৰু সম্মতিৰ বাবে এই চৰকাৰী প্ৰকল্পৰ নথিপত্ৰ পৰীক্ষা কৰক।

নথিপত্ৰৰ বিষয়বস্তু:
{content}

পৰীক্ষা কৰক:
1. বাধ্যতামূলক বিভাগৰ উপস্থিতি
2. আৰ্থিক বিৱৰণৰ সম্পূৰ্ণতা
3. কাৰিকৰী নিৰ্দেশনাৰ পৰ্যাপ্ততা
4. পৰিৱেশগত অনুমতি
5. সময়সূচীৰ সম্ভাৱনা
6. বিপদ প্ৰশমন ব্যৱস্থা

সম্পূৰ্ণতাৰ স্ক'ৰ (0-100) প্ৰদান কৰক আৰ অনুপস্থিত বা অপৰ্যাপ্ত বিভাগৰ তালিকা প্ৰস্তুত কৰক।"""
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the primary language of the document"""
        hindi_matches = len(self.language_patterns['hindi'].findall(text))
        assamese_matches = len(self.language_patterns['assamese'].findall(text))
        english_matches = len(self.language_patterns['english'].findall(text))
        
        total_matches = hindi_matches + assamese_matches + english_matches
        
        if total_matches == 0:
            return 'english'  # Default
        
        # Determine primary language
        if hindi_matches / total_matches > 0.3:
            return 'hindi'
        elif assamese_matches / total_matches > 0.3:
            return 'assamese'
        else:
            return 'english'
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 50000) -> List[str]:
        """Split text into chunks for RAG processing"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    async def analyze_chunk(self, chunk: str, chunk_num: int, total_chunks: int, language: str) -> str:
        """Analyze a single chunk of the document"""
        prompt_template = f"""
You are analyzing part {chunk_num} of {total_chunks} of a government project document.

Extract and summarize key information from this section:
- Important project details
- Budget/cost information  
- Timeline information
- Technical specifications
- Risks or concerns mentioned
- Any other critical information

Be concise but comprehensive.

Document section:
{{content}}
"""
        
        if language == 'hindi':
            prompt_template = f"""
आप एक सरकारी परियोजना दस्तावेज़ के भाग {chunk_num} का {total_chunks} में से विश्लेषण कर रहे हैं।

इस अनुभाग से मुख्य जानकारी निकालें और सारांशित करें:
- महत्वपूर्ण परियोजना विवरण
- बजट/लागत जानकारी
- समयसीमा जानकारी
- तकनीकी विनिर्देश
- उल्लिखित जोखिम या चिंताएं
- कोई अन्य महत्वपूर्ण जानकारी

संक्षिप्त लेकिन व्यापक रहें।

दस्तावेज़ अनुभाग:
{{content}}
"""
        elif language == 'assamese':
            prompt_template = f"""
আপনি এক চৰকাৰী প্ৰকল্পৰ নথিপত্ৰৰ {chunk_num} ভাগৰ {total_chunks} ৰ ভিতৰত বিশ্লেষণ কৰি আছে।

এই বিভাগৰ পৰা মুখ্য তথ্য উলিয়াই সাৰাংশ কৰক:
- গুৰুত্বপূৰ্ণ প্ৰকল্পৰ বিৱৰণ
- বাজেট/খৰচৰ তথ্য
- সময়সূচীৰ তথ্য
- কাৰিকৰী নিৰ্দেশনা
- উল্লেখিত বিপদ বা চিন্তা
- আন যিকোনো গুৰুত্বপূৰ্ণ তথ্য

সংক্ষিপ্ত কিন্তু বিস্তৃত হওক।

নথিপত্ৰৰ বিভাগ:
{{content}}
"""
        
        prompt = prompt_template.format(content=chunk)
        response = await self._generate_with_gemini(prompt)
        return response if response else ""

    async def analyze_document(self, content: str, analysis_type: str = 'analysis') -> Dict[str, Any]:
        """Perform comprehensive RAG-based AI analysis of document content"""
        try:
            # Detect language
            language = self.detect_language(content)
            
            print(f"Processing document with {len(content)} characters using RAG...")
            
            # Split document into chunks for comprehensive analysis
            chunks = self.chunk_text(content, chunk_size=50000)
            print(f"Split into {len(chunks)} chunks for analysis...")
            
            # Analyze each chunk
            chunk_analyses = []
            for i, chunk in enumerate(chunks, 1):
                print(f"Analyzing chunk {i}/{len(chunks)}...")
                analysis = await self.analyze_chunk(chunk, i, len(chunks), language)
                chunk_analyses.append(analysis)
            
            # Combine all chunk analyses
            combined_analysis = "\n\n".join([f"Section {i+1}:\n{analysis}" for i, analysis in enumerate(chunk_analyses)])
            
            print("Generating final comprehensive summary...")
            
            # Generate final comprehensive summary from all chunks
            if analysis_type == 'analysis':
                final_prompt = self._get_comprehensive_analysis_prompt(combined_analysis, language)
            else:
                final_prompt = self._get_validation_prompt(combined_analysis, language)
            
            # Generate analysis using Gemini
            response = await self._generate_with_gemini(final_prompt)
            
            # Parse and structure the response
            result = self._parse_gemini_response(response, analysis_type, language)
            
            # Add metadata
            result['metadata'] = {
                'document_length': len(content),
                'chunks_processed': len(chunks),
                'language_detected': language,
                'analysis_type': analysis_type,
                'timestamp': datetime.utcnow().isoformat(),
                'ai_model': 'gemini-1.5-pro',
                'rag_enabled': True
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _get_comprehensive_analysis_prompt(self, combined_analysis: str, language: str) -> str:
        """Get comprehensive analysis prompt based on language"""
        if language == 'hindi':
            return f"""
निम्नलिखित सरकारी परियोजना दस्तावेज़ के विस्तृत विश्लेषण के आधार पर, प्रदान करें:

1. एक व्यापक कार्यकारी सारांश (5-7 बुलेट पॉइंट्स) जिसमें शामिल हो:
   - परियोजना का उद्देश्य और दायरा
   - मुख्य घटक और डिलिवरेबल्स
   - बजट और वित्तीय पहलू
   - समयसीमा और मील के पत्थर
   - अपेक्षित प्रभाव और लाभ
   - पहचाने गए जोखिम या चिंताएं

2. निम्नलिखित मुख्य मेट्रिक्स निकालें:
   - परियोजना का नाम
   - स्थान
   - कुल बजट/लागत
   - परियोजना की समयसीमा/अवधि

अपनी प्रतिक्रिया को JSON के रूप में प्रारूपित करें:
{{
  "summary": "• बिंदु 1\\n• बिंदु 2\\n• बिंदु 3\\n• बिंदु 4\\n• बिंदु 5",
  "metrics": {{
    "project_name": "निकाला गया नाम या null",
    "location": "निकाला गया स्थान या null",
    "budget": "निकाला गया बजट या null",
    "timeline": "निकाली गई समयसीमा या null"
  }}
}}

सभी दस्तावेज़ अनुभागों से विश्लेषण:
{combined_analysis[:100000]}
"""
        elif language == 'assamese':
            return f"""
নিম্নলিখিত চৰকাৰী প্ৰকল্পৰ নথিপত্ৰৰ বিস্তৃত বিশ্লেষণৰ ভিত্তিত, প্ৰদান কৰক:

1. এক বিস্তৃত কাৰ্যকৰী সাৰাংশ (5-7 বুলেট পইণ্ট) য'ত অন্তৰ্ভুক্ত:
   - প্ৰকল্পৰ উদ্দেশ্য আৰু পৰিসৰ
   - মুখ্য উপাদান আৰু ডেলিভাৰেবল
   - বাজেট আৰু আৰ্থিক দিশ
   - সময়সূচী আৰু মাইলফলক
   - প্ৰত্যাশিত প্ৰভাৱ আৰু সুবিধা
   - চিনাক্ত কৰা বিপদ বা চিন্তা

2. নিম্নলিখিত মুখ্য মেট্ৰিক্স উলিয়াওক:
   - প্ৰকল্পৰ নাম
   - স্থান
   - মুঠ বাজেট/খৰচ
   - প্ৰকল্পৰ সময়সূচী/সময়কাল

আপোনাৰ প্ৰতিক্ৰিয়া JSON হিচাপে বিন্যাস কৰক:
{{
  "summary": "• বিন্দু 1\\n• বিন্দু 2\\n• বিন্দু 3\\n• বিন্দু 4\\n• বিন্দু 5",
  "metrics": {{
    "project_name": "উলিওৱা নাম বা null",
    "location": "উলিওৱা স্থান বা null", 
    "budget": "উলিওৱা বাজেট বা null",
    "timeline": "উলিওৱা সময়সূচী বা null"
  }}
}}

সকলো নথিপত্ৰ বিভাগৰ পৰা বিশ্লেষণ:
{combined_analysis[:100000]}
"""
        else:  # English
            return f"""
Based on the following detailed analysis of all sections of a government project document, provide:

1. A comprehensive executive summary (5-7 bullet points) covering:
   - Project objective and scope
   - Key components and deliverables
   - Budget and financial aspects
   - Timeline and milestones
   - Expected impact and benefits
   - Any risks or concerns identified

2. Extract the following key metrics:
   - Project Name
   - Location
   - Total Budget/Cost
   - Project Timeline/Duration

Format your response as JSON:
{{
  "summary": "• Point 1\\n• Point 2\\n• Point 3\\n• Point 4\\n• Point 5",
  "metrics": {{
    "project_name": "extracted name or null",
    "location": "extracted location or null",
    "budget": "extracted budget or null",
    "timeline": "extracted timeline or null"
  }}
}}

Analysis from all document sections:
{combined_analysis[:100000]}
"""
    
    def _get_validation_prompt(self, combined_analysis: str, language: str) -> str:
        """Get validation prompt based on language"""
        if language == 'hindi':
            return f"""
निम्नलिखित सरकारी परियोजना दस्तावेज़ के विश्लेषण के आधार पर सत्यापन प्रदान करें:

पूर्णता और अनुपालन के लिए जांचें:
1. अनिवार्य अनुभागों की उपस्थिति
2. वित्तीय विवरण की पूर्णता
3. तकनीकी विनिर्देशों की पर्याप्तता
4. पर्यावरणीय मंजूरी
5. समयसीमा की व्यवहार्यता
6. जोखिम शमन उपाय

JSON प्रारूप में प्रदान करें:
{{
  "completeness_score": 85,
  "missing_sections": ["गुम अनुभाग 1", "गुम अनुभाग 2"],
  "recommendations": ["सिफारिश 1", "सिफारिश 2"],
  "compliance_status": "समग्र स्थिति"
}}

दस्तावेज़ विश्लेषण:
{combined_analysis[:100000]}
"""
        elif language == 'assamese':
            return f"""
নিম্নলিখিত চৰকাৰী প্ৰকল্পৰ নথিপত্ৰৰ বিশ্লেষণৰ ভিত্তিত সত্যাপন প্ৰদান কৰক:

সম্পূৰ্ণতা আৰু সম্মতিৰ বাবে পৰীক্ষা কৰক:
1. বাধ্যতামূলক বিভাগৰ উপস্থিতি
2. আৰ্থিক বিৱৰণৰ সম্পূৰ্ণতা
3. কাৰিকৰী নিৰ্দেশনাৰ পৰ্যাপ্ততা
4. পৰিৱেশগত অনুমতি
5. সময়সূচীৰ সম্ভাৱনা
6. বিপদ প্ৰশমন ব্যৱস্থা

JSON বিন্যাসত প্ৰদান কৰক:
{{
  "completeness_score": 85,
  "missing_sections": ["অনুপস্থিত বিভাগ 1", "অনুপস্থিত বিভাগ 2"],
  "recommendations": ["পৰামৰ্শ 1", "পৰামৰ্শ 2"],
  "compliance_status": "সামগ্ৰিক অৱস্থা"
}}

নথিপত্ৰ বিশ্লেষণ:
{combined_analysis[:100000]}
"""
        else:  # English
            return f"""
Based on the following government project document analysis, provide validation:

Check for completeness and compliance:
1. Mandatory sections presence
2. Financial details completeness
3. Technical specifications adequacy
4. Environmental clearances
5. Timeline feasibility
6. Risk mitigation measures

Provide in JSON format:
{{
  "completeness_score": 85,
  "missing_sections": ["Missing section 1", "Missing section 2"],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "compliance_status": "Overall status"
}}

Document analysis:
{combined_analysis[:100000]}
"""
    
    async def analyze_pdf_document(self, pdf_bytes: bytes, analysis_type: str = 'analysis') -> Dict[str, Any]:
        """Analyze PDF document"""
        try:
            # Extract text from PDF
            text_content = self.extract_text_from_pdf(pdf_bytes)
            
            if not text_content.strip():
                raise Exception("No text could be extracted from the PDF")
            
            # Analyze the extracted text
            return await self.analyze_document(text_content, analysis_type)
            
        except Exception as e:
            raise Exception(f"PDF analysis failed: {str(e)}")
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate response using Gemini API"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000,
                )
            )
            
            # Handle different response formats
            try:
                # First try the simple text accessor
                return response.text
            except:
                # If that fails, try extracting from candidates
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        if text_parts:
                            return ' '.join(text_parts)
                
                # If all else fails, return empty string
                return ""
                
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _parse_gemini_response(self, response: str, analysis_type: str, language: str) -> Dict[str, Any]:
        """Parse and structure Gemini response"""
        # Try to parse JSON response first
        try:
            import json
            
            # Remove markdown code blocks if present
            result_text = response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            parsed_json = json.loads(result_text.strip())
            
            if analysis_type == 'analysis':
                # Ensure required keys exist for analysis
                result = {
                    'summary': parsed_json.get('summary', ''),
                    'project_details': parsed_json.get('metrics', {}),
                    'technical_specs': [],
                    'financial_breakdown': {'budget': parsed_json.get('metrics', {}).get('budget', '')},
                    'timeline': [parsed_json.get('metrics', {}).get('timeline', '')],
                    'risks': [],
                    'benefits': [],
                    'compliance': {},
                    'language': language,
                    'metrics': parsed_json.get('metrics', {}),
                    'raw_response': response
                }
                return result
            else:  # validation
                return {
                    'completeness_score': parsed_json.get('completeness_score', 75),
                    'missing_sections': parsed_json.get('missing_sections', []),
                    'recommendations': parsed_json.get('recommendations', []),
                    'compliance_status': parsed_json.get('compliance_status', 'Status not determined'),
                    'language': language,
                    'raw_response': response
                }
                
        except (json.JSONDecodeError, KeyError):
            # Fallback to text parsing if JSON parsing fails
            pass
        
        # Fallback to original text parsing
        if analysis_type == 'analysis':
            return {
                'summary': self._extract_summary(response),
                'project_details': self._extract_project_details(response),
                'technical_specs': self._extract_technical_specs(response),
                'financial_breakdown': self._extract_financial_info(response),
                'timeline': self._extract_timeline(response),
                'risks': self._extract_risks(response),
                'benefits': self._extract_benefits(response),
                'compliance': self._extract_compliance(response),
                'language': language,
                'metrics': {
                    'project_name': self._extract_project_details(response).get('name', ''),
                    'location': self._extract_project_details(response).get('location', ''),
                    'budget': list(self._extract_financial_info(response).get('amounts_found', ['']))[0] if self._extract_financial_info(response).get('amounts_found') else '',
                    'timeline': self._extract_timeline(response)[0] if self._extract_timeline(response) else ''
                },
                'raw_response': response
            }
        else:  # validation
            return {
                'completeness_score': self._extract_completeness_score(response),
                'missing_sections': self._extract_missing_sections(response),
                'recommendations': self._extract_recommendations(response),
                'compliance_status': self._extract_compliance_status(response),
                'language': language,
                'raw_response': response
            }
    
    def _extract_summary(self, text: str) -> str:
        """Extract executive summary from response"""
        # Look for summary sections
        patterns = [
            r'(?i)executive summary[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)summary[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)सारांश[:\s]*(.*?)(?=\n\n|\n|$)',
            r'(?i)সাৰাংশ[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Fallback: return first paragraph
        paragraphs = text.split('\n\n')
        return paragraphs[0] if paragraphs else text[:500]
    
    def _extract_project_details(self, text: str) -> Dict[str, str]:
        """Extract project details from response"""
        details = {}
        
        # Common patterns for project details
        patterns = {
            'name': [r'(?i)project name[:\s]*([^\n]+)', r'(?i)परियोजना का नाम[:\s]*([^\n]+)', r'(?i)প্ৰকল্পৰ নাম[:\s]*([^\n]+)'],
            'location': [r'(?i)location[:\s]*([^\n]+)', r'(?i)स्थान[:\s]*([^\n]+)', r'(?i)স্থান[:\s]*([^\n]+)'],
            'cost': [r'(?i)(?:total )?cost[:\s]*([^\n]+)', r'(?i)लागत[:\s]*([^\n]+)', r'(?i)খৰচ[:\s]*([^\n]+)'],
            'duration': [r'(?i)duration[:\s]*([^\n]+)', r'(?i)अवधि[:\s]*([^\n]+)', r'(?i)সময়কাল[:\s]*([^\n]+)'],
            'agency': [r'(?i)implementing agency[:\s]*([^\n]+)', r'(?i)कार्यान्वयन एजेंसी[:\s]*([^\n]+)', r'(?i)কাৰ্যকৰী সংস্থা[:\s]*([^\n]+)']
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    details[key] = match.group(1).strip()
                    break
        
        return details
    
    def _extract_technical_specs(self, text: str) -> List[str]:
        """Extract technical specifications"""
        specs = []
        
        # Look for technical specification sections
        patterns = [
            r'(?i)technical specifications?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)तकनीकी विनिर्देश[:\s]*(.*?)(?=\n\n|\n|$)',
            r'(?i)কাৰিকৰী নিৰ্দেশনা[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Split into individual specs
                specs.extend([line.strip() for line in content.split('\n') if line.strip()])
                break
        
        return specs[:10]  # Limit to top 10 specs
    
    def _extract_financial_info(self, text: str) -> Dict[str, str]:
        """Extract financial information"""
        financial = {}
        
        # Look for cost patterns
        cost_patterns = [
            r'(?i)rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*crores?',
            r'(?i)₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*crores?',
            r'(?i)(\d+(?:,\d+)*(?:\.\d+)?)\s*crores?'
        ]
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, text)
            if matches:
                financial['amounts_found'] = matches
                break
        
        return financial
    
    def _extract_timeline(self, text: str) -> List[str]:
        """Extract timeline information"""
        timeline = []
        
        # Look for timeline patterns
        patterns = [
            r'(?i)phase \d+[:\s]*([^\n]+)',
            r'(?i)month[s]? \d+[:\s]*([^\n]+)',
            r'(?i)चरण \d+[:\s]*([^\n]+)',
            r'(?i)পৰ্যায় \d+[:\s]*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            timeline.extend(matches)
        
        return timeline[:5]  # Limit to 5 timeline items
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risk information"""
        risks = []
        
        # Look for risk patterns
        patterns = [
            r'(?i)risks?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)जोखिम[:\s]*(.*?)(?=\n\n|\n|$)',
            r'(?i)বিপদ[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                risks.extend([line.strip() for line in content.split('\n') if line.strip()])
                break
        
        return risks[:5]  # Limit to top 5 risks
    
    def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits information"""
        benefits = []
        
        # Look for benefits patterns
        patterns = [
            r'(?i)benefits?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)लाभ[:\s]*(.*?)(?=\n\n|\n|$)',
            r'(?i)সুবিধা[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                benefits.extend([line.strip() for line in content.split('\n') if line.strip()])
                break
        
        return benefits[:5]  # Limit to top 5 benefits
    
    def _extract_compliance(self, text: str) -> Dict[str, str]:
        """Extract compliance information"""
        compliance = {}
        
        # Look for compliance patterns
        patterns = {
            'environmental': [r'(?i)environmental clearance[:\s]*([^\n]+)', r'(?i)पर्यावरणीय मंजूरी[:\s]*([^\n]+)'],
            'regulatory': [r'(?i)regulatory approval[:\s]*([^\n]+)', r'(?i)नियामक अनुमोदन[:\s]*([^\n]+)']
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    compliance[key] = match.group(1).strip()
                    break
        
        return compliance
    
    def _extract_completeness_score(self, text: str) -> int:
        """Extract completeness score from validation response"""
        patterns = [
            r'(?i)completeness score[:\s]*(\d+)',
            r'(?i)score[:\s]*(\d+)',
            r'(?i)(\d+)%',
            r'(?i)(\d+)/100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return 75  # Default score if not found
    
    def _extract_missing_sections(self, text: str) -> List[str]:
        """Extract missing sections from validation response"""
        missing = []
        
        patterns = [
            r'(?i)missing[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)absent[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)गुम[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                missing.extend([line.strip() for line in content.split('\n') if line.strip()])
                break
        
        return missing
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from validation response"""
        recommendations = []
        
        patterns = [
            r'(?i)recommendations?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)suggestions?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)सिफारिशें[:\s]*(.*?)(?=\n\n|\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                recommendations.extend([line.strip() for line in content.split('\n') if line.strip()])
                break
        
        return recommendations
    
    def _extract_compliance_status(self, text: str) -> str:
        """Extract overall compliance status"""
        patterns = [
            r'(?i)compliance status[:\s]*([^\n]+)',
            r'(?i)overall status[:\s]*([^\n]+)',
            r'(?i)अनुपालन स्थिति[:\s]*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Status not determined"


# Global service instance
simple_gemini_service = SimpleGeminiService()


# Convenience functions for API compatibility
async def generate_summary(document_content: str) -> Dict[str, Any]:
    """Generate summary from text content"""
    result = await simple_gemini_service.analyze_document(document_content, 'analysis')
    
    # Add metrics for backward compatibility
    result['metrics'] = {
        'total_cost': result.get('financial_breakdown', {}).get('amounts_found', ['Not specified'])[0] if result.get('financial_breakdown', {}).get('amounts_found') else 'Not specified',
        'duration': result.get('project_details', {}).get('duration', 'Not specified'),
        'location': result.get('project_details', {}).get('location', 'Not specified'),
        'completeness_score': 85,  # Default score
        'language_detected': result.get('language', 'english')
    }
    
    return result


async def analyze_pdf_document(pdf_bytes: bytes) -> Dict[str, Any]:
    """Analyze PDF document"""
    return await simple_gemini_service.analyze_pdf_document(pdf_bytes, 'analysis')


async def validate_pdf_document(pdf_bytes: bytes) -> Dict[str, Any]:
    """Validate PDF document"""
    return await simple_gemini_service.analyze_pdf_document(pdf_bytes, 'validation')