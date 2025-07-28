from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_community.llms import LLM
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import requests
import json
from typing import Any, List, Mapping, Optional
from django.conf import settings

class TalkBotLLM(LLM):
    """سفارشی سازی LLM برای API تاک‌بات"""
    
    api_url: str = settings.TALKBOT_API_URL
    api_key: str = settings.TALKBOT_API_KEY
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    
    @property
    def _llm_type(self) -> str:
        return "talkbot"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "stream": False,
            "max_tokens": 4000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"خطا در دریافت پاسخ: {str(e)}"
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model": self.model, "temperature": self.temperature}

class MedicalAgent:
    """Agent تخصصی پزشکی"""
    
    def __init__(self):
        self.llm = TalkBotLLM()
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True
        )
        
        # ابزارهای تخصصی
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """ایجاد ابزارهای تخصصی پزشکی"""
        
        def symptom_analyzer(symptoms: str) -> str:
            """تحلیل علائم بیمار"""
            prompt = f"""
            شما یک متخصص تحلیل علائم هستید. علائم زیر را تحلیل کنید:
            {symptoms}
            
            لطفاً موارد زیر را ارائه دهید:
            1. علائم اصلی و فرعی
            2. احتمالی ترین علل
            3. علائم خطرناک که نیاز به مراجعه فوری دارند
            4. سؤالات تکمیلی برای بهتر شدن تشخیص
            
            پاسخ به فارسی و کاملاً علمی باشد.
            """
            return self.llm._call(prompt)
        
        def urgency_assessor(case_info: str) -> str:
            """ارزیابی میزان اورژانسی"""
            prompt = f"""
            بر اساس اطلاعات زیر، میزان اورژانسی را ارزیابی کنید:
            {case_info}
            
            سطوح اورژانسی:
            - کم: می‌تواند چند روز صبر کند
            - متوسط: در عرض 24-48 ساعت
            - بالا: در عرض چند ساعت
            - اورژانسی: فوری و بدون تأخیر
            
            پاسخ دهید: سطح اورژانسی + دلیل
            """
            return self.llm._call(prompt)
        
        def medication_checker(medications: str) -> str:
            """بررسی تداخل دارویی"""
            prompt = f"""
            داروهای زیر را بررسی کنید:
            {medications}
            
            موارد بررسی:
            1. تداخلات دارویی احتمالی
            2. عوارض جانبی مهم
            3. توصیه‌های مصرف
            4. موارد احتیاط
            
            پاسخ علمی و دقیق ارائه دهید.
            """
            return self.llm._call(prompt)
        
        def differential_diagnosis(symptoms_and_history: str) -> str:
            """تشخیص افتراقی"""
            prompt = f"""
            بر اساس علائم و سابقه زیر، تشخیص‌های افتراقی ارائه دهید:
            {symptoms_and_history}
            
            لطفاً موارد زیر را شامل کنید:
            1. احتمالی‌ترین تشخیص‌ها به ترتیب احتمال
            2. آزمایش‌های تشخیصی پیشنهادی
            3. علائم تأییدی یا رد کننده
            4. اقدامات اولیه
            
            تأکید: این فقط اطلاع‌رسانی است و جایگزین ویزیت پزشک نیست.
            """
            return self.llm._call(prompt)
        
        return [
            Tool(
                name="symptom_analyzer",
                description="تحلیل علائم بیمار و ارائه توضیحات تخصصی",
                func=symptom_analyzer
            ),
            Tool(
                name="urgency_assessor", 
                description="ارزیابی میزان اورژانسی موردبر اساس علائم",
                func=urgency_assessor
            ),
            Tool(
                name="medication_checker",
                description="بررسی تداخلات دارویی و عوارض جانبی",
                func=medication_checker
            ),
            Tool(
                name="differential_diagnosis",
                description="ارائه تشخیص‌های افتراقی بر اساس علائم و سابقه",
                func=differential_diagnosis
            )
        ]
    
    def _create_agent(self):
        """ایجاد Agent اصلی"""
        
        template = """
        شما یک دستیار هوشمند پزشکی هستید که با ابزارهای تخصصی مجهز شده‌اید.
        
        وظایف شما:
        1. شرح حال کامل بیمار را بگیرید
        2. از ابزارهای تخصصی برای تحلیل استفاده کنید
        3. سؤالات هدفمند بپرسید
        4. اطلاعات علمی و کاربردی ارائه دهید
        5. همیشه تأکید کنید که جایگزین پزشک نیستید
        
        ابزارهای در دسترس: {tools}
        
        تاریخچه مکالمه: {chat_history}
        
        سؤال/درخواست کاربر: {input}
        
        فکر: {agent_scratchpad}
        
        لطفاً پاسخ جامع و تخصصی ارائه دهید.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "chat_history", "agent_scratchpad"],
            partial_variables={"tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])}
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    def process_message(self, message: str, conversation_history: List = None) -> str:
        """پردازش پیام کاربر"""
        
        # اگر تاریخچه ارائه شده، آن را به memory اضافه کن
        if conversation_history:
            for msg in conversation_history:
                if msg['role'] == 'user':
                    self.memory.chat_memory.add_user_message(msg['content'])
                elif msg['role'] == 'assistant':
                    self.memory.chat_memory.add_ai_message(msg['content'])
        
        # اجرای agent
        agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        try:
            result = agent_executor.invoke({"input": message})
            return result['output']
        except Exception as e:
            return f"متأسفانه خطایی رخ داد: {str(e)}. لطفاً سؤال خود را مجدداً مطرح کنید."

class MedicalKnowledgeBase:
    """پایگاه دانش پزشکی"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.vectorstore = None
        self._initialize_kb()
    
    def _initialize_kb(self):
        """راه‌اندازی پایگاه دانش"""
        # در اینجا می‌توانید متون پزشکی را از فایل یا دیتابیس بارگذاری کنید
        medical_texts = [
            "علائم سردرد شامل درد در ناحیه سر، حساسیت به نور و صدا می‌باشد.",
            "تب معمولاً نشانه عفونت در بدن است و بالای 38 درجه خطرناک محسوب می‌شود.",
            "درد قفسه سینه می‌تواند نشانه مشکلات قلبی، ریوی یا گوارشی باشد.",
            # اضافه کردن متون بیشتر...
        ]
        
        try:
            self.vectorstore = Chroma.from_texts(
                texts=medical_texts,
                embedding=self.embeddings,
                persist_directory=settings.MEDICAL_KB_PATH
            )
        except Exception as e:
            print(f"خطا در راه‌اندازی پایگاه دانش: {e}")
    
    def search(self, query: str, k: int = 3):
        """جستجو در پایگاه دانش"""
        if self.vectorstore:
            return self.vectorstore.similarity_search(query, k=k)
        return []