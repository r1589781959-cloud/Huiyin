"""
回音 - 技能系统抽象基类
所有技能（Skill）必须实现此接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Any = None           # 返回的数据（供 LLM 融入对话）
    error: Optional[str] = None
    display_text: str = ""     # 可选：直接展示给用户的文本


class Skill(ABC):
    """技能抽象基类"""

    name: str = ""
    description: str = ""      # 告诉 LLM 这个技能能做什么
    parameters: Dict = {}      # JSON Schema 格式的参数定义
    permissions: List[str] = []

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> SkillResult:
        raise NotImplementedError

    def to_function_schema(self) -> Dict:
        """转换为 LLM function calling 的 schema 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class SkillRegistry:
    """技能注册表，管理所有已启用的技能"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_schemas(self) -> List[Dict]:
        """返回所有技能的 function schema（注入 system prompt 用）"""
        return [s.to_function_schema() for s in self._skills.values()]

    def list_names(self) -> List[str]:
        return list(self._skills.keys())
