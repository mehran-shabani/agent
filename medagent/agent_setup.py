"""
Agent setup for MedAgent.

This module initializes a LangChain agent with a small set of tools. The
agent uses a zero-shot ReAct strategy and a simple chat model.
"""

from langchain.agents import initialize_agent, AgentType
from medagent.tools import (
    GetPatientSummaryTool, SummarizeSessionTool,
    ImageAnalysisTool, ProfanityCheckTool
)
from medagent.talkbot_llm import TalkBotLLM  # 👈 LLM جدید

TOOLS = [
    GetPatientSummaryTool(),
    SummarizeSessionTool(),
    ImageAnalysisTool(),
    ProfanityCheckTool(),
]

llm = TalkBotLLM(model="o3-mini")

agent = initialize_agent(
    tools=TOOLS,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
