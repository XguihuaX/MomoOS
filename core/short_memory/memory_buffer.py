# memory_buffer.py 用于控制短期记忆，支持按 user_id 分隔

from collections import defaultdict

# 使用 defaultdict 管理每个用户的短期记忆列表
short_term_memory = defaultdict(list)

# 最多保留 N 条（可选，防止内存溢出）
MAX_MEMORY_PER_USER = 50

def add_to_short_term(user_id: str, role: str, text: str):
    memory_list = short_term_memory[user_id]
    memory_list.append({
        "role": role,  # 可为 "user"、"system" 等
        "text": text
    })
    # 如果超过最大条目限制，自动移除最早的记录
    if len(memory_list) > MAX_MEMORY_PER_USER:
        memory_list.pop(0)

def get_short_term(user_id: str):
    return short_term_memory.get(user_id, [])

def clear_short_term(user_id: str):
    if user_id in short_term_memory:
        short_term_memory[user_id].clear()
