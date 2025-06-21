# prompt_state.py
from collections import defaultdict
from .prompt_builder import CHARACTER_CONFIG, build_prompt
from ..logger import logger

class PromptManager:
    def __init__(self):
        self.user_characters = defaultdict(lambda: "默认")

    def get_prompt(self, user_id: str):
        character_id = self.user_characters[user_id]
        logger.info(f"当前角色获取：{user_id=} -> {character_id=}")
        return build_prompt(character_id)


    def switch_character(self, user_id: str, character_id: str) -> bool:
        logger.info(f" 切换角色：{user_id=} -> {character_id=}")
        if character_id in CHARACTER_CONFIG:
            self.user_characters[user_id] = character_id
            return True
        return False


    def get_current_character(self, user_id: str) -> str:
        return self.user_characters[user_id]

prompt_manager = PromptManager()
