import os
import time
try:
    import pyautogui
    pyautogui_available = True
except Exception as e:
    print(f"[警告] 无法导入 pyautogui：{e}")
    pyautogui = None
    pyautogui_available = False


## macOS 网易云音乐控制器（需前提条件：GUI 环境 & 已安装网易云）
class NeteaseMusicController:
    def __init__(self, app_path="/Applications/NeteaseMusic.app"):
        self.app_path = app_path
        self.app_name = "NeteaseMusic"
        self.enabled = pyautogui_available and os.path.exists(self.app_path)

        if not self.enabled:
            print("⚠️ 当前环境不支持 GUI 或网易云未安装，控制功能将禁用")

    def launch(self):
        if not os.path.exists(self.app_path):
            return "❌ 没有找到网易云音乐应用"
        subprocess.run(["open", self.app_path])
        return "✅ 已打开网易云音乐"

    def activate(self):
        if not self.enabled:
            return
        subprocess.run(["osascript", "-e", f'tell application "{self.app_name}" to activate'])
        time.sleep(0.2)

    def play_pause(self):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        pyautogui.press('space')
        return "播放 / 暂停已切换"

    def previous_track(self):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        time.sleep(0.1)
        pyautogui.keyDown('command')
        pyautogui.press('right')
        pyautogui.keyUp('command')
        return "已切换到上一首"

    def next_track(self):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        pyautogui.keyDown('command')
        pyautogui.press('left')
        pyautogui.keyUp('command')
        return "已切换到下一首"

    def volume_up(self):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        pyautogui.keyDown('command')
        pyautogui.press('up')
        pyautogui.keyUp('command')
        return "提高声音"

    def volume_down(self):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        pyautogui.keyDown('command')
        pyautogui.press('down')
        pyautogui.keyUp('command')
        return "降低声音"

    def search_song(self, song_name: str):
        if not self.enabled:
            return "❌ 当前环境不支持模拟控制"
        self.activate()
        pyautogui.keyDown('command')
        pyautogui.press('f')
        pyautogui.keyUp('command')
        pyautogui.typewrite(song_name, interval=0.05)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1.2)
        return f"🎵 已搜索歌曲：{song_name}"


### ---------- ChatAgent角色 相关操作----------###
from ..core.llm.prompt_state import prompt_manager

def switch_character(character_id: str, user_id: str) -> str:
    success = prompt_manager.switch_character(user_id, character_id)
    if success:
        return f"✅ 角色已切换为「{character_id}」。"
    return f"❌ 未找到名为「{character_id}」的角色。"




import subprocess
import threading



def mac_notify(title: str, text: str):

    """
    使用 AppleScript 在 macOS 上发送系统通知
    """
    try:
        script = f'display notification "{text}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
    except Exception as e:
        print(f"[通知失败] {e}")

def alarm(text: str):
    """
    使用 macOS 原生命令 say 进行语音播报（避免 pyttsx3 的 run loop 冲突）
    """
    # ✅ 系统通知
    try:
        script = f'display notification "{text}" with title \"🔔 闹钟提醒\"'
        subprocess.run(["osascript", "-e", script])
    except Exception as e:
        print(f"[通知失败] {e}")

    # ✅ 用 say 播报，系统一定有声音
    def speak():
        try:
            subprocess.run(["say", text])
        except Exception as e:
            print(f"[say 播报失败] {e}")

    threading.Thread(target=speak).start()
    print(f"[提醒触发 - say 播报中] {text}")


from ..core.short_memory.memory_buffer import clear_short_term as _clear

def clear_short_term(user_id: str) -> str:
    _clear(user_id)
    return "✅ 已清除当前用户的短期记忆"
