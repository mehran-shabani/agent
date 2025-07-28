"""
Agent setup for MedAgent.

This module initializes a LangChain agent with a small set of tools. The
agent uses a zero-shot ReAct strategy and a simple chat model.
"""

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from medagent.tools import (
    GetPatientSummaryTool, SummarizeSessionTool,
    ImageAnalysisTool, ProfanityCheckTool
)

TOOLS = [
    GetPatientSummaryTool(),
    SummarizeSessionTool(),
    ImageAnalysisTool(),
    ProfanityCheckTool(),
]

llm = ChatOpenAI(model_name="o3-mini", temperature=0.1)

agent = initialize_agent(
    tools=TOOLS,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
