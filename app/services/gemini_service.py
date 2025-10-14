"""
Gemini AI Service with RAG-based document analysis for large PDFs
Supports multilingual analysis (English, Hindi, Assamese)
"""
import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import PyPDF2
from io import BytesIO

from ..core.config import settings


class GeminiRAGService:
    """RAG-based AI service using Gemini for document analysis"""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Initialize embedding model for RAG
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
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

Please provide:
1. Executive Summary (2-3 paragraphs)
2. Key Project Details:
   - Project Name
   - Location
   - Total Cost
   - Duration
   - Implementing Agency
3. Technical Specifications
4. Financial Breakdown
5. Timeline and Phases
6. Risk Assessment
7. Expected Benefits
8. Compliance Status

Format the response as structured JSON with clear sections.""",
                
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

कृपया प्रदान करें:
1. कार्यकारी सारांश (2-3 पैराग्राफ)
2. मुख्य परियोजना विवरण:
   - परियोजना का नाम
   - स्थान
   - कुल लागत
   - अवधि
   - कार्यान्वयन एजेंसी
3. तकनीकी विनिर्देश
4. वित्तीय विवरण
5. समयसीमा और चरण
6. जोखिम मूल्यांकन
7. अपेक्षित लाभ
8. अनुपालन स्थिति

स्पष्ट अनुभागों के साथ संरचित JSON के रूप में प्रतिक्रिया को प्रारूपित करें।""",
                
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

অনুগ্ৰহ কৰি প্ৰদান কৰক:
1. কাৰ্যকৰী সাৰাংশ (2-3 অনুচ্ছেদ)
2. মুখ্য প্ৰকল্পৰ বিৱৰণ:
   - প্ৰকল্পৰ নাম
   - স্থান
   - মুঠ খৰচ
   - সময়কাল
   - কাৰ্যকৰী সংস্থা
3. কাৰিকৰী নিৰ্দেশনা
4. আৰ্থিক বিভাজন
5. সময়সূচী আৰু পৰ্যায়
6. বিপদৰ মূল্যায়ন
7. প্ৰত্যাশিত সুবিধা
8. সম্মতিৰ অৱস্থা

স্পষ্ট বিভাগৰ সৈতে গঠনমূলক JSON হিচাপে প্ৰতিক্ৰিয়া বিন্যাস কৰক।""",
                
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

সম্পূৰ্ণতাৰ স্ক'ৰ (0-100) প্ৰদান কৰক আৰু অনুপস্থিত বা অপৰ্যাপ্ত বিভাগৰ তালিকা প্ৰস্তুত কৰক।"""
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
    
    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for RAG processing"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for i in range(end - 100, min(end + 100, len(text))):
                    if text[i] in '.!?।':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def create_vector_store(self, chunks: List[str]) -> Tuple[faiss.IndexFlatIP, np.ndarray]:
        """Create FAISS vector store from text chunks"""
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        embeddings = embeddings.astype('float32')
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        return index, embeddings
    
    def retrieve_relevant_chunks(self, query: str, index: faiss.IndexFlatIP, 
                                chunks: List[str], top_k: int = 5) -> List[str]:
        """Retrieve most relevant chunks for a query"""
        # Encode query
        query_embedding = self.embedding_model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search for similar chunks
        scores, indices = index.search(query_embedding, top_k)
        
        # Return relevant chunks
        relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
        return relevant_chunks
    
    async def analyze_document_with_rag(self, pdf_bytes: bytes, 
                                       analysis_type: str = 'analysis') -> Dict[str, Any]:
        """Perform RAG-based analysis of large PDF documents"""
        try:
            # Extract text from PDF
            full_text = self.extract_text_from_pdf(pdf_bytes)
            
            if not full_text.strip():
                raise Exception("No text could be extracted from the PDF")
            
            # Detect language
            language = self.detect_language(full_text)
            
            # Chunk the document
            chunks = self.chunk_text(full_text)
            
            if not chunks:
                raise Exception("Document could not be chunked properly")
            
            # Create vector store
            index, embeddings = self.create_vector_store(chunks)
            
            # Define analysis queries based on type
            if analysis_type == 'analysis':
                queries = [
                    "project name, location, cost, duration, implementing agency",
                    "technical specifications, design parameters, infrastructure details",
                    "financial breakdown, budget allocation, cost estimates",
                    "timeline, phases, milestones, implementation schedule",
                    "environmental impact, clearances, mitigation measures",
                    "social benefits, economic impact, beneficiaries",
                    "risk assessment, challenges, mitigation strategies"
                ]
            else:  # validation
                queries = [
                    "mandatory sections, required documents, compliance requirements",
                    "financial details completeness, budget justification",
                    "technical specifications adequacy, design standards",
                    "environmental clearances, impact assessment",
                    "timeline feasibility, resource availability",
                    "risk mitigation, contingency planning"
                ]
            
            # Retrieve relevant content for each query
            relevant_content = []
            for query in queries:
                relevant_chunks = self.retrieve_relevant_chunks(query, index, chunks, top_k=3)
                relevant_content.extend(relevant_chunks)
            
            # Combine relevant content (remove duplicates)
            combined_content = "\n\n".join(list(dict.fromkeys(relevant_content)))
            
            # Limit content size for Gemini API
            max_content_length = 30000  # Adjust based on Gemini limits
            if len(combined_content) > max_content_length:
                combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"
            
            # Get appropriate prompt
            prompt_template = self.prompts[language][analysis_type]
            prompt = prompt_template.format(content=combined_content)
            
            # Generate analysis using Gemini
            response = await self._generate_with_gemini(prompt)
            
            # Parse and structure the response
            result = self._parse_gemini_response(response, analysis_type, language)
            
            # Add metadata
            result['metadata'] = {
                'document_length': len(full_text),
                'chunks_processed': len(chunks),
                'language_detected': language,
                'analysis_type': analysis_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"RAG analysis failed: {str(e)}")
    
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
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _parse_gemini_response(self, response: str, analysis_type: str, language: str) -> Dict[str, Any]:
        """Parse and structure Gemini response"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
        except:
            pass
        
        # Fallback: structure the response manually
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
        
        return 0  # Default if not found
    
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
gemini_rag_service = GeminiRAGService()


# Convenience functions for backward compatibility
async def generate_summary(document_content: str) -> Dict[str, Any]:
    """Generate summary from text content (for backward compatibility)"""
    # Convert text to bytes for PDF processing simulation
    text_bytes = document_content.encode('utf-8')
    
    # Create a simple text-based analysis
    language = gemini_rag_service.detect_language(document_content)
    
    # Use Gemini directly for text analysis
    prompt_template = gemini_rag_service.prompts[language]['analysis']
    prompt = prompt_template.format(content=document_content[:30000])  # Limit content
    
    try:
        response = await gemini_rag_service._generate_with_gemini(prompt)
        result = gemini_rag_service._parse_gemini_response(response, 'analysis', language)
        
        # Add metrics for backward compatibility
        result['metrics'] = {
            'total_cost': gemini_rag_service._extract_financial_info(response).get('amounts_found', ['Not specified'])[0] if gemini_rag_service._extract_financial_info(response).get('amounts_found') else 'Not specified',
            'duration': gemini_rag_service._extract_project_details(response).get('duration', 'Not specified'),
            'location': gemini_rag_service._extract_project_details(response).get('location', 'Not specified'),
            'completeness_score': 85,  # Default score
            'language_detected': language
        }
        
        return result
        
    except Exception as e:
        raise Exception(f"Summary generation failed: {str(e)}")


async def analyze_pdf_document(pdf_bytes: bytes) -> Dict[str, Any]:
    """Analyze PDF document using RAG"""
    return await gemini_rag_service.analyze_document_with_rag(pdf_bytes, 'analysis')


async def validate_pdf_document(pdf_bytes: bytes) -> Dict[str, Any]:
    """Validate PDF document using RAG"""
    return await gemini_rag_service.analyze_document_with_rag(pdf_bytes, 'validation')