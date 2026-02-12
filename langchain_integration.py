"""LANGCHAIN集成模块"""
import os
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import OpenAI
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

# 初始化缓存
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

class LangChainIntegration:
    """LANGCHAIN集成类"""
    
    def __init__(self, api_key=None, model_name="gpt-3.5-turbo"):
        """初始化LANGCHAIN集成
        
        Args:
            api_key: OpenAI API密钥
            model_name: 模型名称
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.3
        )
    
    def summarize_text(self, text, user_prompt="", system_prompt=""):
        """使用LANGCHAIN进行文本总结
        
        Args:
            text: 要总结的文本
            user_prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            总结结果
        """
        # 构建提示词模板
        if not system_prompt:
            system_prompt = "你是一个专业的文本总结助手，能够准确提炼文本的核心内容，生成简洁明了的总结。"
        
        if not user_prompt:
            user_prompt = "请对以下文本进行总结，要求：\n1. 提炼核心内容和关键信息\n2. 保持逻辑清晰，结构完整\n3. 使用简洁明了的语言\n4. 不包含冗余信息\n\n文本内容：\n{text}"
        
        # 创建提示词模板
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(user_prompt)
        ])
        
        # 创建输出解析器
        output_parser = StrOutputParser()
        
        # 构建链
        chain = prompt_template | self.llm | output_parser
        
        # 执行链
        result = chain.invoke({"text": text})
        
        return result
    
    def transcribe_video(self, video_file, language="zh"):
        """使用LANGCHAIN进行视频转写
        
        Args:
            video_file: 视频文件路径
            language: 语言
            
        Returns:
            转写结果
        """
        # 这里我们仍然使用Whisper模型进行转写
        # 但可以通过LANGCHAIN来管理这个过程
        import whisper
        
        # 加载Whisper模型
        model = whisper.load_model("tiny")
        
        # 执行转写
        result = model.transcribe(
            video_file,
            language=language,
            fp16=False,
            verbose=False,
            task="transcribe",
            beam_size=1,
            temperature=0.0,
            best_of=1,
            patience=0.0,
            initial_prompt="请使用标准简体中文进行转写。",
            condition_on_previous_text=False,
            compression_ratio_threshold=2.4
        )
        
        return result
    
    def process_video(self, video_file, user_prompt=""):
        """完整的视频处理流程
        
        Args:
            video_file: 视频文件路径
            user_prompt: 用户提示词
            
        Returns:
            处理结果
        """
        # 1. 转写视频
        transcribe_result = self.transcribe_video(video_file)
        
        # 2. 提取转写文本
        text = transcribe_result["text"]
        segments = []
        for seg in transcribe_result["segments"]:
            segments.append({
                "start_time": seg["start"],
                "text": seg["text"].strip()
            })
        
        # 3. 总结文本
        summary = self.summarize_text(text, user_prompt)
        
        return {
            "segments": segments,
            "ai_summary": summary,
            "transcribe_text": text
        }
