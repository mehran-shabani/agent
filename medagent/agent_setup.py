"""
Agent setup for MedAgent.

This module initializes a LangChain agent with a small set of tools. The
agent uses a zero-shot ReAct strategy and a simple chat model.
"""

from langchain.agents import initialize_agent, AgentType

# Import tools as classes (should inherit from BaseTool)
from medagent.tools import (
    GetPatientSummaryTool,
    SummarizeSessionTool,
    ImageAnalysisTool,
    ProfanityCheckTool,
)

from medagent.talkbot_llm import TalkBotLLM  # Custom LLM wrapper

# Instantiate tool objects (must be class-based tools)
TOOLS = [
    GetPatientSummaryTool(),
    SummarizeSessionTool(),
    ImageAnalysisTool(),
    ProfanityCheckTool(),
]

# Instantiate LLM (customized for TalkBot API)
llm = TalkBotLLM(model="o3-mini")

# Initialize agent with zero-shot ReAct
agent = initialize_agent(
    tools=TOOLS,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
