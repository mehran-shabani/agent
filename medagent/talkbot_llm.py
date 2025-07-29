from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation
from typing import List
from medagent.talkbot_client import tb_chat  # فرض بر این است که تعریف شده

class TalkBotLLM(BaseLLM):
    model: str = "o3-mini"

    def _call(self, prompt: str, stop: List[str] = None) -> str:
        # ساختار پیام سازگار با chat models
        messages = [{"role": "user", "content": prompt}]
        return tb_chat(messages, model=self.model)

    def _generate(self, prompts: List[str], stop: List[str] = None) -> List[Generation]:
        return [Generation(text=self._call(prompt, stop)) for prompt in prompts]

    @property
    def _llm_type(self) -> str:
        return "talkbot"
