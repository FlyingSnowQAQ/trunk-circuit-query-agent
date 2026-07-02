"""
DeepSeek API 封装

提供三个核心 LLM 调用：
1. analyze_intent   — 从自然语言中提取系统名 / 电路编号
2. format_summary   — 将结构化的查询结果转为友好文字总结
3. fuzzy_correct    — 系统名纠错（备用）
"""
import json
import httpx
from typing import Optional

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT


class LLMClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.model = DEEPSEEK_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def available(self) -> bool:
        """LLM 是否可用"""
        return bool(self.api_key)

    def _call_llm(self, system_prompt: str, user_prompt: str = "",
                  max_tokens: int = 1024, temperature: float = None) -> str:
        """通用 LLM 调用"""
        if not self.api_key:
            raise RuntimeError("DeepSeek API key 未配置")

        messages = [{"role": "system", "content": system_prompt}]
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature if temperature is not None else LLM_TEMPERATURE,
        }

        with httpx.Client(timeout=LLM_TIMEOUT) as client:
            resp = client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    def analyze_intent(self, user_input: str) -> dict:
        """
        从用户自然语言输入中提取查询意图

        返回:
            {
                "intent": str,       # search_system / search_circuit_no / search_detail
                "system_name": str,  # 提取的系统名
                "circuit_no": str,   # 提取的电路号
                "confidence": float, # 置信度
            }
        """
        system_prompt = """你是一个中国移动干线电路查询系统的意图识别模块。你的任务是从用户输入中提取查询意图和参数。

请输出严格的 JSON 格式（不要markdown包裹），格式如下：
{
    "intent": "search_system" 或 "search_circuit_no" 或 "search_detail",
    "system_name": "提取出的传输系统名，没提取到填空字符串",
    "circuit_no": "提取出的电路编号，没提取到填空字符串",
    "confidence": 0.0-1.0 之间的置信度
}

规则：
- 如果用户提到系统名（如"北京-上海39系统""北京-上海W-44""W-239"等），intent 为 search_system
- 如果用户只提数字且像是电路编号（如"4950""B0167"），intent 为 search_circuit_no
- 如果用户说"展开""详情""路由"等，intent 为 search_detail
- system_name 提取时去掉"查一下""路由""详情"等无关词，保留核心名称
- 如果无法识别，system_name 填空字符串
"""
        try:
            text = self._call_llm(system_prompt, user_input, max_tokens=256)
            # 尝试解析 JSON
            parsed = json.loads(text)
            return {
                "intent": parsed.get("intent", ""),
                "system_name": parsed.get("system_name", ""),
                "circuit_no": parsed.get("circuit_no", ""),
                "confidence": float(parsed.get("confidence", 0)),
            }
        except (json.JSONDecodeError, Exception) as e:
            return {"intent": "unknown", "system_name": user_input,
                    "circuit_no": "", "confidence": 0.0, "error": str(e)}

    def format_summary(self, query: str, steps: list) -> str:
        """
        将结构化的步骤结果转为友好的文字总结

        参数:
            query:  用户原始输入
            steps:  三步推理的结果列表

        返回:
            友好的文字总结
        """
        system_prompt = """你是一个中国移动干线电路查询助手，请根据查询结果生成简洁清晰的总结。

请以"以下是【系统名】的查询结果"开头，然后分三步呈现：
1. 识别到的传输系统名
2. 所属工程期数（明确说明属于第几期）
3. 路由详情总结（有多少跳、关键站点等）

如果路由有设备级端口信息，也一并说明。
如果没有路由详情，请告知。
语言用中文，语气专业友好。"""

        user_prompt = f"""用户查询：{query}

查询步骤结果（JSON）：
{json.dumps(steps, ensure_ascii=False, indent=2)}

请根据以上结果生成文字总结。"""

        try:
            return self._call_llm(system_prompt, user_prompt, max_tokens=1024)
        except Exception:
            return ""

    def fuzzy_correct(self, raw_name: str) -> str:
        """
        当 SQL 搜索无结果时，尝试让 LLM 纠正系统名

        返回:
            纠正后的系统名
        """
        system_prompt = f"""你是中国移动干线电路查询系统的名称纠错模块。

用户输入了一个传输系统名："{raw_name}"

但数据库中未找到该名称。请尝试以下纠正策略：
1. 移除可能的错别字或多余字符
2. 补全常见的系统名格式（如"北京-上海39系统"格式）
3. 解析缩写或变体（如"京沪39"→"北京-上海39系统"）

请直接输出你认为最可能的正确系统名，不要有任何解释和额外文字。
只输出名称本身。"""

        try:
            corrected = self._call_llm(system_prompt, max_tokens=64, temperature=0.1)
            corrected = corrected.strip().strip('"\'「」 ').strip()
            if len(corrected) >= 4:
                return corrected
        except Exception:
            pass
        return raw_name
