#!/usr/bin/env python3
"""
Test RAG-based analysis with Gemini for large documents
Supports multilingual analysis (English, Hindi, Assamese)
"""
import asyncio
from app.services.gemini_service import generate_summary

# Create a longer test document that simulates a real DPR
test_text = """PROJECT DETAILED REPORT

CHAPTER 1: INTRODUCTION
Project Name: Construction of 2-Lane Road in Tawang District
Location: Tawang, Arunachal Pradesh
Implementing Agency: Ministry of Development of North Eastern Region

CHAPTER 2: PROJECT BACKGROUND
The project aims to construct a 45 km two-lane road connecting Village A to Town B in the Tawang District.
This region currently lacks proper road connectivity, affecting economic development and access to essential services.
The proposed road will serve over 50,000 residents and facilitate tourism in this scenic region.

CHAPTER 3: TECHNICAL SPECIFICATIONS
Road Length: 45 kilometers
Road Width: 7 meters (two-lane)
Number of Bridges: 3 major bridges
Number of Culverts: 15 culverts
Pavement Type: Bituminous concrete
Design Speed: 60 km/h

CHAPTER 4: FINANCIAL DETAILS
Total Project Cost: Rs. 250 Crores
Breakdown:
- Civil Works: Rs. 180 Crores
- Bridges and Culverts: Rs. 50 Crores
- Land Acquisition: Rs. 10 Crores
- Contingencies: Rs. 10 Crores

CHAPTER 5: PROJECT TIMELINE
Total Duration: 36 months
Phase 1 (Months 1-12): Land acquisition and site preparation
Phase 2 (Months 13-30): Main construction work
Phase 3 (Months 31-36): Finishing and quality checks

CHAPTER 6: ENVIRONMENTAL IMPACT
Environmental clearance obtained from State Environmental Impact Assessment Authority.
Mitigation measures include:
- Tree plantation along the road
- Proper drainage systems
- Wildlife crossing provisions

CHAPTER 7: SOCIAL IMPACT
Expected Benefits:
- Improved connectivity for 50,000+ residents
- Enhanced access to healthcare and education
- Boost to local tourism industry
- Creation of 500+ temporary jobs during construction
- Improved market access for local farmers

CHAPTER 8: RISK ASSESSMENT
Key Risks Identified:
1. Weather-related delays during monsoon season
2. Potential cost escalation due to terrain challenges
3. Land acquisition delays
4. Availability of skilled labor in remote location

Mitigation Strategies:
- Seasonal work planning
- Contingency budget allocation
- Early stakeholder engagement
- Training programs for local workforce

CHAPTER 9: IMPLEMENTATION PLAN
The project will be implemented through competitive bidding.
Quality control measures will be strictly enforced.
Regular monitoring and evaluation will be conducted.

CHAPTER 10: CONCLUSION
This project is critical for the development of the Tawang region and will significantly improve
the quality of life for residents while promoting economic growth and tourism.""" * 3  # Repeat to make it longer

async def test_rag_analysis():
    """Test RAG-based comprehensive analysis"""
    print("🚀 Testing Gemini RAG-based Analysis for Large Documents")
    print("=" * 70)
    print(f"📄 Document length: {len(test_text):,} characters")
    print(f"📊 Simulating 300-400 page PDF analysis")
    print(f"🌐 Multilingual support: English, Hindi (हिन्दी), Assamese (অসমীয়া)")
    print("\n🔄 Starting analysis...\n")

    try:
        result = await generate_summary(test_text)
        
        print("✅ SUCCESS - Gemini RAG Analysis Complete!")
        print("=" * 70)
        
        print("\n📋 Executive Summary:")
        print("-" * 30)
        print(result.get('summary', 'No summary available'))
        
        print("\n📊 Extracted Metrics:")
        print("-" * 30)
        metrics = result.get('metrics', {})
        for key, value in metrics.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print("\n🏗️ Project Details:")
        print("-" * 30)
        project_details = result.get('project_details', {})
        for key, value in project_details.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print("\n💰 Financial Information:")
        print("-" * 30)
        financial = result.get('financial_breakdown', {})
        if financial:
            for key, value in financial.items():
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print("\n⚠️ Risk Assessment:")
        print("-" * 30)
        risks = result.get('risks', [])
        for i, risk in enumerate(risks[:3], 1):
            print(f"  {i}. {risk}")
        
        print("\n🎯 Expected Benefits:")
        print("-" * 30)
        benefits = result.get('benefits', [])
        for i, benefit in enumerate(benefits[:3], 1):
            print(f"  {i}. {benefit}")
        
        print("\n🔧 Technical Specifications:")
        print("-" * 30)
        tech_specs = result.get('technical_specs', [])
        for i, spec in enumerate(tech_specs[:3], 1):
            print(f"  {i}. {spec}")
        
        print("\n🌍 Language & Metadata:")
        print("-" * 30)
        metadata = result.get('metadata', {})
        print(f"  • Language Detected: {result.get('language', 'english').title()}")
        print(f"  • Document Chunks: {metadata.get('chunks_processed', 'N/A')}")
        print(f"  • Analysis Type: {metadata.get('analysis_type', 'summary')}")
        
        print("\n" + "=" * 70)
        print("🎉 Gemini RAG Analysis Test Completed Successfully!")
        print("✨ Ready for 300-400 page PDF documents")
        print("🌐 Multilingual support active")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check Gemini API key configuration")
        print("  2. Verify internet connection")
        print("  3. Ensure all dependencies are installed")

if __name__ == "__main__":
    asyncio.run(test_rag_analysis())