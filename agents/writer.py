# agents/writer.py
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

from tools.report_tools import generate_pdf_report
from prompts import WRITER_PROMPT, WRITER_SYSTEM, RECOMMENDATION_PROMPT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WriterAgent:
    """Agent responsible for synthesizing research and analysis into final report"""
    
    def __init__(self, api_key: str = None):
        """Initialize writer agent with Gemini LLM"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.4,  # Balanced creativity for writing
            convert_system_message_to_human=True
        )
        
        logger.info("WriterAgent initialized")
    
    def write_report(self, ticker: str, research_data: Dict, analysis_data: Dict) -> Dict[str, Any]:
        """
        Main writing method - synthesizes all data into final report
        """
        try:
            logger.info(f"📝 Writing report for {ticker}")
            
            # Step 1: Generate recommendation
            logger.info("🔄 Generating investment recommendation...")
            recommendation = self._generate_recommendation(ticker, research_data, analysis_data)
            logger.info(f"✅ Recommendation generated: {recommendation.get('rating')} with {recommendation.get('confidence')} confidence")
            
            # Step 2: Write full report
            logger.info("🔄 Writing comprehensive report...")
            report_content = self._write_full_report(ticker, research_data, analysis_data, recommendation)
            logger.info("✅ Report content written")
            
            # Step 3: Generate PDF
            logger.info("🔄 Generating PDF report...")
            chart_paths = analysis_data.get('chart_paths', [])
            pdf_path = generate_pdf_report(
                ticker=ticker,
                company_data=analysis_data.get('financial_data', {}),
                news_data=research_data.get('news_data', {}),
                analysis_summary=report_content.get('summary', ''),
                recommendation=recommendation.get('summary', 'Hold'),
                chart_paths=chart_paths
            )
            
            # Log PDF status
            if pdf_path and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024  # Size in KB
                logger.info(f"✅ PDF report saved: {pdf_path} ({file_size:.1f} KB)")
            else:
                logger.warning("⚠️ PDF generation failed or file not found")
            
            # Step 4: Compile final output
            writer_output = {
                'ticker': ticker,
                'company_name': analysis_data.get('company_name', ticker),
                'report_summary': report_content.get('summary', ''),
                'executive_summary': report_content.get('executive_summary', ''),
                'key_findings': report_content.get('key_findings', []),
                'investment_thesis': report_content.get('thesis', ''),
                'bull_case': report_content.get('bull_case', ''),
                'bear_case': report_content.get('bear_case', ''),
                'recommendation': recommendation,
                'risk_factors': report_content.get('risks', []),
                'catalysts': report_content.get('catalysts', []),
                'pdf_path': pdf_path,
                'full_report': report_content.get('full_text', ''),
                'generated_at': datetime.now().isoformat()
            }
            
            # Log summary
            logger.info(f"✅ Report writing completed for {ticker}")
            logger.info(f"📊 Key Findings: {len(writer_output['key_findings'])} | Risks: {len(writer_output['risk_factors'])}")
            
            return writer_output
            
        except Exception as e:
            logger.error(f"❌ Error in report writing: {str(e)}")
            return {
                'ticker': ticker,
                'report_summary': f"Error during report writing: {str(e)}",
                'pdf_path': None,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_recommendation(self, ticker: str, research_data: Dict, analysis_data: Dict) -> Dict[str, Any]:
        """Generate investment recommendation"""
        try:
            # Prepare summaries
            research_summary = research_data.get('research_summary', 'No research summary available')
            analysis_summary = analysis_data.get('analysis_summary', 'No analysis summary available')
            
            # Get recommendation from LLM
            messages = [
                SystemMessage(content="You are an investment recommendation expert. Provide clear, data-driven recommendations."),
                HumanMessage(content=RECOMMENDATION_PROMPT.format(
                    ticker=ticker,
                    research_summary=research_summary,
                    analysis_summary=analysis_summary
                ))
            ]
            
            response = self.llm.invoke(messages)
            
            # Try to parse JSON response
            try:
                # Find JSON in response
                text = response.content
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    recommendation = json.loads(json_str)
                    logger.info(f"✅ JSON recommendation parsed successfully")
                else:
                    # Fallback
                    logger.warning("⚠️ No JSON found in response, using fallback parsing")
                    recommendation = self._parse_recommendation_fallback(text)
            except Exception as json_error:
                logger.warning(f"⚠️ JSON parsing failed: {str(json_error)}, using fallback")
                recommendation = self._parse_recommendation_fallback(response.content)
            
            # Ensure all fields exist
            default_recommendation = {
                'rating': recommendation.get('rating', 'HOLD'),
                'confidence': recommendation.get('confidence', 'Medium'),
                'target_price': recommendation.get('target_price', None),
                'time_horizon': recommendation.get('time_horizon', 'Medium'),
                'summary': recommendation.get('summary', f'{ticker} analysis complete')
            }
            
            return default_recommendation
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {str(e)}")
            return {
                'rating': 'HOLD',
                'confidence': 'Medium',
                'target_price': None,
                'time_horizon': 'Medium',
                'summary': f'Analysis complete for {ticker}'
            }
    
    def _write_full_report(self, ticker: str, research_data: Dict, analysis_data: Dict, recommendation: Dict) -> Dict[str, Any]:
        """Write complete investment report"""
        try:
            messages = [
                SystemMessage(content=WRITER_SYSTEM),
                HumanMessage(content=WRITER_PROMPT.format(
                    ticker=ticker,
                    research_data=json.dumps(research_data, indent=2, default=str),
                    analysis_data=json.dumps(analysis_data, indent=2, default=str)
                ))
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the report
            report = self._parse_report(response.content, recommendation)
            logger.info(f"✅ Report parsed into {len(report['key_findings'])} findings and {len(report['risks'])} risks")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error writing full report: {str(e)}")
            return {
                'summary': f'Analysis complete for {ticker}',
                'executive_summary': f'Analysis of {ticker} based on latest data',
                'key_findings': ['Analysis completed'],
                'thesis': 'See summary',
                'bull_case': '',
                'bear_case': '',
                'risks': ['Market volatility', 'Company-specific risks'],
                'catalysts': ['Earnings reports', 'Market developments'],
                'full_text': response.content if 'response' in locals() else ''
            }
    
    def _parse_recommendation_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback parsing for recommendation when JSON fails"""
        text_upper = text.upper()
        
        # Determine rating
        if 'BUY' in text_upper and 'SELL' not in text_upper:
            rating = 'BUY'
        elif 'SELL' in text_upper:
            rating = 'SELL'
        else:
            rating = 'HOLD'
        
        # Determine confidence
        if 'HIGH CONFIDENCE' in text_upper:
            confidence = 'High'
        elif 'LOW CONFIDENCE' in text_upper:
            confidence = 'Low'
        else:
            confidence = 'Medium'
        
        # Try to extract target price
        target_price = None
        import re
        price_pattern = r'\$?(\d+\.?\d*)'
        prices = re.findall(price_pattern, text)
        if prices:
            try:
                target_price = float(prices[0])
            except:
                pass
        
        return {
            'rating': rating,
            'confidence': confidence,
            'target_price': target_price,
            'time_horizon': 'Medium',
            'summary': text[:200] + '...' if len(text) > 200 else text
        }
    
    def _parse_report(self, text: str, recommendation: Dict) -> Dict[str, Any]:
        """Parse the full report into sections"""
        report = {
            'summary': '',
            'executive_summary': '',
            'key_findings': [],
            'thesis': '',
            'bull_case': '',
            'bear_case': '',
            'risks': [],
            'catalysts': [],
            'full_text': text
        }
        
        lines = text.split('\n')
        current_section = 'summary'
        
        for line in lines:
            line_lower = line.lower()
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Detect sections
            if 'executive summary' in line_lower:
                current_section = 'executive'
                continue
            elif 'key finding' in line_lower or 'key takeaway' in line_lower:
                current_section = 'findings'
                continue
            elif 'investment thesis' in line_lower:
                current_section = 'thesis'
                continue
            elif 'bull case' in line_lower or 'positive' in line_lower:
                current_section = 'bull'
                continue
            elif 'bear case' in line_lower or 'risk' in line_lower:
                current_section = 'bear'
                continue
            elif 'risk factor' in line_lower:
                current_section = 'risks'
                continue
            elif 'catalyst' in line_lower:
                current_section = 'catalysts'
                continue
            
            # Add content to current section
            if current_section == 'executive':
                report['executive_summary'] += line_stripped + ' '
            elif current_section == 'thesis':
                report['thesis'] += line_stripped + ' '
            elif current_section == 'bull':
                report['bull_case'] += line_stripped + ' '
            elif current_section == 'bear':
                report['bear_case'] += line_stripped + ' '
            elif current_section == 'findings' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                # Clean bullet points
                clean_finding = line_stripped.lstrip('-•*‣▪→ ').strip()
                if clean_finding:
                    report['key_findings'].append(clean_finding)
            elif current_section == 'findings' and line_stripped and line_stripped[0].isdigit() and line_stripped[1:2] in ['.', ')']:
                # Handle numbered lists
                clean_finding = line_stripped[2:].strip() if len(line_stripped) > 2 else line_stripped
                if clean_finding:
                    report['key_findings'].append(clean_finding)
            elif current_section == 'risks' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_risk = line_stripped.lstrip('-•*‣▪→ ').strip()
                if clean_risk:
                    report['risks'].append(clean_risk)
            elif current_section == 'catalysts' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_catalyst = line_stripped.lstrip('-•*‣▪→ ').strip()
                if clean_catalyst:
                    report['catalysts'].append(clean_catalyst)
            elif current_section == 'summary':
                report['summary'] += line_stripped + ' '
        
        # Clean up whitespace
        for key in ['summary', 'executive_summary', 'thesis', 'bull_case', 'bear_case']:
            report[key] = report[key].strip()
        
        # If no findings found, add a default
        if not report['key_findings'] and report['summary']:
            # Try to extract first few sentences as findings
            sentences = report['summary'].split('. ')
            report['key_findings'] = [s.strip() + '.' for s in sentences[:3] if len(s) > 20]
        
        return report