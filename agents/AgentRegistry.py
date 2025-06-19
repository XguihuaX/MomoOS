from agents.ToolAgent import ToolAgent
from agents.MemoryAgent import MemoryAgent
from agents.ChatAgent import ChatAgent
from agents.SearchAgent import SearchAgent

class AgentRegistry:
    def __init__(self):
        self._agents = {}

    def register(self, name: str, agent):
        """
        注册一个 Agent 实例。
        :param name: Agent 的唯一名称（如 "ToolAgent"）
        :param agent: 该 Agent 的实例对象
        """
        self._agents[name] = agent

    def get(self, name: str):
        """
        根据名称获取注册的 Agent。
        :param name: Agent 名称
        :return: Agent 实例或 None
        """
        return self._agents.get(name)

    def all(self):
        """
        获取所有已注册的 Agent 字典。
        :return: dict[name] = agent
        """
        return self._agents

    def register_default_agents(self):
        """
        快捷注册默认内置的 Agent 集合。
        """
        self.register("ToolAgent", ToolAgent())
        self.register("MemoryAgent", MemoryAgent())
        self.register("ChatAgent", ChatAgent())
        self.register("SearchAgent", SearchAgent())