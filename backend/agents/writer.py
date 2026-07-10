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
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
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
        """Write complete investment report as JSON and assemble full text"""
        try:
            messages = [
                SystemMessage(content="You are a senior financial writer who outputs structured financial JSON data. Output raw JSON ONLY."),
                HumanMessage(content=WRITER_PROMPT.format(
                    ticker=ticker,
                    research_data=json.dumps(research_data, indent=2, default=str),
                    analysis_data=json.dumps(analysis_data, indent=2, default=str)
                ))
            ]
            
            response = self.llm.invoke(messages)
            text = response.content.strip()
            
            data = None
            try:
                # Find and load JSON block
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    data = json.loads(json_str)
                    logger.info("✅ Report JSON parsed successfully")
            except Exception as je:
                logger.warning(f"⚠️ Report JSON parsing failed: {str(je)}. Falling back to text parser.")
                
            if data and isinstance(data, dict):
                # Build the markdown full text dynamically for PDF/Download representation
                full_text = f"""## Investment Report: {ticker}
**Date:** {datetime.now().strftime("%B %d, %Y")}

### 1. EXECUTIVE SUMMARY
{data.get('executive_summary', '')}

### 2. KEY FINDINGS
"""
                for item in data.get('key_findings', []):
                    full_text += f"- {item}\n"
                    
                full_text += f"""
### 3. INVESTMENT THESIS
{data.get('investment_thesis', '')}

**Bull Case:**
"""
                for item in data.get('bull_case', []):
                    full_text += f"- {item}\n"
                    
                full_text += "\n**Bear Case:**\n"
                for item in data.get('bear_case', []):
                    full_text += f"- {item}\n"
                    
                full_text += f"""
### 4. FINAL RECOMMENDATION
*   **Recommendation:** {recommendation.get('rating', 'HOLD')}
*   **Confidence Level:** {recommendation.get('confidence', 'Medium')}
*   **Target Price Range:** {recommendation.get('target_price') if recommendation.get('target_price') else 'N/A'}
*   **Time Horizon:** {recommendation.get('time_horizon', 'Medium')}

**Key Catalysts to Watch:**
"""
                for item in data.get('catalysts', []):
                    full_text += f"- {item}\n"
                    
                full_text += "\n### 5. RISK FACTORS\n"
                for item in data.get('risk_factors', []):
                    full_text += f"- {item}\n"
                    
                thesis_data = data.get('investment_thesis', '')
                thesis_raw = thesis_data
                if isinstance(thesis_data, dict):
                    thesis_str = ""
                    if 'bull_case' in thesis_data:
                        thesis_str += "**Bull Case:**\n"
                        bulls = thesis_data['bull_case']
                        if isinstance(bulls, list):
                            thesis_str += "\n".join(f"- {b}" for b in bulls) + "\n\n"
                        else:
                            thesis_str += f"{bulls}\n\n"
                    if 'bear_case' in thesis_data:
                        thesis_str += "**Bear Case:**\n"
                        bears = thesis_data['bear_case']
                        if isinstance(bears, list):
                            thesis_str += "\n".join(f"- {b}" for b in bears) + "\n\n"
                        else:
                            thesis_str += f"{bears}\n\n"
                    if not thesis_str:
                        thesis_str = str(thesis_data)
                    thesis_data = thesis_str

                bull_case = data.get('bull_case', [])
                if not bull_case and isinstance(thesis_raw, dict):
                    bull_case = thesis_raw.get('bull_case', [])

                bear_case = data.get('bear_case', [])
                if not bear_case and isinstance(thesis_raw, dict):
                    bear_case = thesis_raw.get('bear_case', [])

                # Compile parsed dict
                report = {
                    'summary': full_text[:400] + '...',
                    'executive_summary': data.get('executive_summary', ''),
                    'key_findings': data.get('key_findings', []),
                    'thesis': thesis_data,
                    'bull_case': bull_case,
                    'bear_case': bear_case,
                    'risks': data.get('risk_factors', []),
                    'catalysts': data.get('catalysts', []),
                    'full_text': full_text
                }
                return report
            else:
                # Fallback to parsing raw text if LLM failed to output JSON
                return self._parse_report_fallback(text, recommendation)
                
        except Exception as e:
            logger.error(f"❌ Error writing full report: {str(e)}")
            return {
                'summary': f'Analysis complete for {ticker}',
                'executive_summary': f'Analysis of {ticker} based on latest data',
                'key_findings': ['Analysis completed'],
                'thesis': 'See summary',
                'bull_case': ['Potential upside based on market cap'],
                'bear_case': ['Potential downside risks'],
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

    def _parse_report_fallback(self, text: str, recommendation: Dict) -> Dict[str, Any]:
        """Fallback markdown parser if JSON output failed"""
        report = {
            'summary': '',
            'executive_summary': '',
            'key_findings': [],
            'thesis': '',
            'bull_case': [],
            'bear_case': [],
            'risks': [],
            'catalysts': [],
            'full_text': text
        }
        
        lines = text.split('\n')
        current_section = 'summary'
        import re
        
        for line in lines:
            line_lower = line.lower()
            line_stripped = line.strip()
            
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
            elif 'bear case' in line_lower or 'risk factor' in line_lower:
                if 'risk factor' in line_lower:
                    current_section = 'risks'
                else:
                    current_section = 'bear'
                continue
            elif 'risk' in line_lower:
                current_section = 'risks'
                continue
            elif 'catalyst' in line_lower:
                current_section = 'catalysts'
                continue
                
            # Add content
            if current_section == 'executive':
                report['executive_summary'] += line_stripped + ' '
            elif current_section == 'thesis':
                report['thesis'] += line_stripped + ' '
            elif current_section == 'bull' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_item = re.sub(r'^[-\u2022*‣▪→]\s*', '', line_stripped).strip()
                if clean_item:
                    report['bull_case'].append(clean_item)
            elif current_section == 'bull':
                report['bull_case'].append(line_stripped)
            elif current_section == 'bear' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_item = re.sub(r'^[-\u2022*‣▪→]\s*', '', line_stripped).strip()
                if clean_item:
                    report['bear_case'].append(clean_item)
            elif current_section == 'bear':
                report['bear_case'].append(line_stripped)
            elif current_section == 'findings' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_finding = re.sub(r'^[-\u2022*‣▪→]\s*', '', line_stripped).strip()
                if clean_finding:
                    report['key_findings'].append(clean_finding)
            elif current_section == 'findings' and line_stripped and line_stripped[0].isdigit() and line_stripped[1:2] in ['.', ')']:
                clean_finding = line_stripped[2:].strip() if len(line_stripped) > 2 else line_stripped
                if clean_finding:
                    report['key_findings'].append(clean_finding)
            elif current_section == 'risks' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_risk = re.sub(r'^[-\u2022*‣▪→]\s*', '', line_stripped).strip()
                if clean_risk:
                    report['risks'].append(clean_risk)
            elif current_section == 'catalysts' and line_stripped and line_stripped[0] in ['-', '•', '*', '‣', '▪', '→']:
                clean_catalyst = re.sub(r'^[-\u2022*‣▪→]\s*', '', line_stripped).strip()
                if clean_catalyst:
                    report['catalysts'].append(clean_catalyst)
            elif current_section == 'summary':
                report['summary'] += line_stripped + ' '
                
        # Clean up whitespace
        for key in ['summary', 'executive_summary', 'thesis']:
            report[key] = report[key].strip()
            
        return report
    