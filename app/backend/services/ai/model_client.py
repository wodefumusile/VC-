"""
OpenAI Compatible API 客户端

支持: DeepSeek, OpenAI, 通义千问 等兼容 API
所有配置通过环境变量管理，禁止硬编码。
"""

from openai import OpenAI
from loguru import logger

from backend.config import settings


class ModelClient:
    """AI 模型客户端 — OpenAI 兼容接口"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
        )
        self.model = settings.AI_MODEL
        logger.info("ModelClient 初始化 | base_url={} | model={}",
                     settings.AI_BASE_URL, settings.AI_MODEL)

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """发送聊天请求，返回响应文本

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户消息
            temperature: 温度参数 (0.0-2.0)

        Returns:
            AI 生成的文本内容

        Raises:
            RuntimeError: API 调用失败
        """
        try:
            logger.info("调用 AI API | model={} | prompt_len={}", self.model, len(user_prompt))

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=4096,
            )

            content = response.choices[0].message.content or ""

            usage = response.usage
            logger.success("AI 调用成功 | tokens: prompt={}, completion={}, total={}",
                            usage.prompt_tokens if usage else "N/A",
                            usage.completion_tokens if usage else "N/A",
                            usage.total_tokens if usage else "N/A")

            return content

        except Exception as e:
            logger.exception("AI API 调用失败")
            raise RuntimeError(f"AI API 调用失败: {str(e)}") from e


# 全局单例
model_client = ModelClient()
