# graph/workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
from datetime import datetime
import logging

from agents.researcher import ResearcherAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state structure
class AgentState(TypedDict):
    """State maintained throughout the agent workflow"""
    # Input
    ticker: str
    company_name: Optional[str]
    
    # Research phase outputs
    research_data: Optional[Dict[str, Any]]
    research_status: str  # "pending", "completed", "failed"
    research_error: Optional[str]
    
    # Analysis phase outputs
    analysis_data: Optional[Dict[str, Any]]
    analysis_status: str  # "pending", "completed", "failed"
    analysis_error: Optional[str]
    
    # Writing phase outputs
    writer_data: Optional[Dict[str, Any]]
    writer_status: str  # "pending", "completed", "failed"
    writer_error: Optional[str]
    
    # Final outputs
    final_report: Optional[str]
    pdf_path: Optional[str]
    
    # Metadata
    start_time: Optional[str]
    end_time: Optional[str]
    messages: Annotated[List[str], operator.add]  # For logging/UI updates

class FinlyzeWorkflow:
    """LangGraph workflow for Finlyze multi-agent system"""
    
    def __init__(self, api_key: str = None):
        """Initialize the workflow with all agents"""
        self.api_key = api_key
        
        # Initialize agents
        self.researcher = ResearcherAgent(api_key)
        self.analyst = AnalystAgent(api_key)
        self.writer = WriterAgent(api_key)
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info("FinlyzeWorkflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Initialize the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("run_researcher", self._run_researcher)
        workflow.add_node("run_analyst", self._run_analyst)
        workflow.add_node("run_writer", self._run_writer)
        
        # Add edges
        workflow.set_entry_point("run_researcher")
        workflow.add_edge("run_researcher", "run_analyst")
        workflow.add_edge("run_analyst", "run_writer")
        workflow.add_edge("run_writer", END)
        
        # Add conditional edges based on failures
        workflow.add_conditional_edges(
            "run_researcher",
            self._check_researcher_status,
            {
                "completed": "run_analyst",
                "failed": END
            }
        )
        
        workflow.add_conditional_edges(
            "run_analyst",
            self._check_analyst_status,
            {
                "completed": "run_writer",
                "failed": END
            }
        )
        
        return workflow.compile()
    
    def _run_researcher(self, state: AgentState) -> AgentState:
        """Run the researcher agent"""
        ticker = state["ticker"]
        company_name = state.get("company_name", "")
        
        logger.info(f"Running researcher for {ticker}")
        
        # Add message
        state["messages"] = state.get("messages", []) + [f"🔍 Researching {ticker} news and sentiment..."]
        
        try:
            # Run research
            research_output = self.researcher.research(ticker, company_name)
            
            # Update state
            state["research_data"] = research_output
            state["research_status"] = "completed"
            
            # Add success message
            news_count = len(research_output.get('news_data', {}).get('news', []))
            sentiment = research_output.get('news_data', {}).get('sentiment', {}).get('overall', 'neutral')
            state["messages"] = state["messages"] + [
                f"✅ Found {news_count} news articles",
                f"📊 Overall sentiment: {sentiment.upper()}"
            ]
            
        except Exception as e:
            logger.error(f"Researcher failed: {str(e)}")
            state["research_status"] = "failed"
            state["research_error"] = str(e)
            state["messages"] = state["messages"] + [f"❌ Research failed: {str(e)}"]
        
        return state
    
    def _run_analyst(self, state: AgentState) -> AgentState:
        """Run the analyst agent"""
        ticker = state["ticker"]
        
        logger.info(f"Running analyst for {ticker}")
        
        # Add message
        state["messages"] = state.get("messages", []) + [f"📈 Analyzing financial data for {ticker}..."]
        
        try:
            # Run analysis
            analysis_output = self.analyst.analyze(ticker)
            
            # Update state
            state["analysis_data"] = analysis_output
            state["analysis_status"] = "completed"
            
            # Add success message
            current_price = analysis_output.get('financial_data', {}).get('current_price')
            pe_ratio = analysis_output.get('financial_data', {}).get('pe_ratio')
            
            price_msg = f"💰 Current price: ${current_price:.2f}" if current_price else ""
            pe_msg = f"📊 P/E Ratio: {pe_ratio:.2f}" if pe_ratio else ""
            
            messages = ["✅ Financial analysis complete"]
            if price_msg:
                messages.append(price_msg)
            if pe_msg:
                messages.append(pe_msg)
            
            state["messages"] = state["messages"] + messages
            
            # Add chart info
            chart_count = len(analysis_output.get('chart_paths', []))
            if chart_count > 0:
                state["messages"] = state["messages"] + [f"📸 Generated {chart_count} charts"]
            
        except Exception as e:
            logger.error(f"Analyst failed: {str(e)}")
            state["analysis_status"] = "failed"
            state["analysis_error"] = str(e)
            state["messages"] = state["messages"] + [f"❌ Analysis failed: {str(e)}"]
        
        return state
    
    def _run_writer(self, state: AgentState) -> AgentState:
        """Run the writer agent"""
        ticker = state["ticker"]
        
        logger.info(f"Running writer for {ticker}")
        
        # Add message
        state["messages"] = state.get("messages", []) + [f"✍️ Writing final report for {ticker}..."]
        
        try:
            # Run writer
            writer_output = self.writer.write_report(
                ticker,
                state["research_data"],
                state["analysis_data"]
            )
            
            # Update state
            state["writer_data"] = writer_output
            state["writer_status"] = "completed"
            state["final_report"] = writer_output.get('report_summary', '')
            state["pdf_path"] = writer_output.get('pdf_path')
            
            # Add success message
            recommendation = writer_output.get('recommendation', {}).get('rating', 'HOLD')
            confidence = writer_output.get('recommendation', {}).get('confidence', 'Medium')
            
            state["messages"] = state["messages"] + [
                f"✅ Report complete!",
                f"🎯 Recommendation: {recommendation} ({confidence} confidence)",
                f"📄 PDF saved to: {writer_output.get('pdf_path', 'N/A')}"
            ]
            
        except Exception as e:
            logger.error(f"Writer failed: {str(e)}")
            state["writer_status"] = "failed"
            state["writer_error"] = str(e)
            state["messages"] = state["messages"] + [f"❌ Report writing failed: {str(e)}"]
        
        # Add end time
        state["end_time"] = datetime.now().isoformat()
        
        return state
    
    def _check_researcher_status(self, state: AgentState) -> str:
        """Check if researcher completed successfully"""
        return "completed" if state.get("research_status") == "completed" else "failed"
    
    def _check_analyst_status(self, state: AgentState) -> str:
        """Check if analyst completed successfully"""
        return "completed" if state.get("analysis_status") == "completed" else "failed"
    
    def run(self, ticker: str, company_name: str = "") -> Dict[str, Any]:
        """
        Run the complete workflow for a ticker
        
        Args:
            ticker: Stock ticker symbol
            company_name: Optional company name for better search
            
        Returns:
            Final state dictionary with all results
        """
        logger.info(f"Starting workflow for {ticker}")
        
        # Initialize state
        initial_state = {
            "ticker": ticker.upper().strip(),
            "company_name": company_name,
            "research_data": None,
            "research_status": "pending",
            "research_error": None,
            "analysis_data": None,
            "analysis_status": "pending",
            "analysis_error": None,
            "writer_data": None,
            "writer_status": "pending",
            "writer_error": None,
            "final_report": None,
            "pdf_path": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "messages": [f"🚀 Starting Finlyze analysis for {ticker}..."]
        }
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            logger.info(f"Workflow completed for {ticker}")
            return final_state
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            initial_state["research_status"] = "failed"
            initial_state["research_error"] = str(e)
            initial_state["messages"] = initial_state["messages"] + [f"❌ Workflow failed: {str(e)}"]
            return initial_state
    
    def get_workflow_graph(self):
        """Return the compiled graph for visualization"""
        return self.graph