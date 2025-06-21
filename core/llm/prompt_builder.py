# prompt_builder.py

from ..constants import CHARACTER_CONFIG, BASE_INSTRUCTION

def build_prompt(character_id="默认"):
    cfg = CHARACTER_CONFIG.get(character_id, CHARACTER_CONFIG["默认"])
    system_prompt = f"{cfg['persona']}\n\n{BASE_INSTRUCTION}"
    return {
        "character_id": character_id,
        "system_prompt": system_prompt,
        "default_emotion": cfg["default_emotion"]
    }
