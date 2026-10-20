import logging
import json
from flask import current_app
from openai import OpenAI

logger = logging.getLogger(__name__)


def call_llm_with_prompt(prompt, max_tokens=4096):
    """
    AI 评分调用函数 - 使用 DeepSeek V4-Pro
    """
    api_key = current_app.config.get('OPENAI_API_KEY')
    model = current_app.config.get('DEFAULT_MODEL', 'deepseek-v4-pro')
    api_timeout = current_app.config.get('API_TIMEOUT', 120)

    if not api_key:
        error_msg = "未配置 API Key"
        logger.error(error_msg)
        return f"错误：{error_msg}"

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
            timeout=api_timeout,
            extra_body={"thinking": {"type": "disabled"}}
        )
        reply = response.choices[0].message.content or ""
        if not reply and hasattr(response.choices[0].message, 'reasoning_content'):
            reply = response.choices[0].message.reasoning_content or ""
        logger.info(f"AI评分调用成功，回复长度: {len(reply)}")
        return reply
    except Exception as e:
        logger.error(f"AI评分调用失败: {str(e)}")
        return f"API 调用失败: {str(e)}"


def call_llm_and_execute(messages, model='deepseek-v4-pro'):
    """
    AI 助手调用函数 - 使用 DeepSeek V4-Pro
    """
    api_key = current_app.config.get('OPENAI_API_KEY')
    api_timeout = current_app.config.get('API_TIMEOUT', 240)

    if not api_key:
        error_msg = "❌ 未配置 API Key"
        logger.error(error_msg)
        return error_msg, None, None

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=16384,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
            timeout=api_timeout
        )
        reply = response.choices[0].message.content or ""
        # 如果content为空，尝试从reasoning_content中提取最终答案
        if not reply and hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning = response.choices[0].message.reasoning_content or ""
            if reasoning:
                # 从思考内容中提取最后一段作为答案
                lines = reasoning.strip().split('\n')
                reply = '\n'.join(lines[-10:]) if len(lines) > 10 else reasoning
        logger.info(f"AI助手调用成功(Think High)，回复长度: {len(reply)}")
        return reply, None, None
    except Exception as e:
        logger.error(f"AI助手调用失败: {str(e)}")
        return f"❌ API 调用失败: {str(e)}", None, None