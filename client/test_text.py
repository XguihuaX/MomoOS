import requests
import base64
import tempfile
import platform
import subprocess

#  配置项
SERVER_URL = "http://106.75.127.211:5001/api/dispatch"
USER_ID = "测试用户003"  # 可更改为不同测试 ID

def play_audio(audio_path):
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", audio_path])
        elif system == "Linux":
            subprocess.run(["aplay", audio_path])
        elif system == "Windows":
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
        else:
            print("⚠️ 当前系统不支持自动播放：", system)
    except Exception as e:
        print("❌ 播放失败：", e)

def send_text_to_server(user_text):
    payload = {
        "source": "frontend",
        "text": user_text,
        "user_id": USER_ID
    }

    try:
        print(f"\n📤 发送内容（用户 {USER_ID}）：{user_text}")
        response = requests.post(SERVER_URL, json=payload)
        response.raise_for_status()

        print("📨 请求状态码：", response.status_code)
        result = response.json()

        # 文本输出
        reply_text = result.get("text", "(无文本)")
        character = result.get("character", "未知角色")
        print(f"🧬 角色：{character}")
        print(f"🤖 回复：{reply_text}")

        # 音频播放
        audio_b64 = result.get("audio")
        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                temp_path = f.name
            print("🎧 音频保存于：", temp_path)
            play_audio(temp_path)
        else:
            print("🔇 无语音内容。")

    except requests.exceptions.RequestException as e:
        print("❌ 请求失败:", e)

def main():
    print("🎙️ ChatAgent 测试终端（输入 exit/quit 退出）")
    while True:
        user_input = input("\n🧑 你：")
        if user_input.strip().lower() in {"exit", "quit"}:
            print("👋 已退出测试。")
            break
        send_text_to_server(user_input)

if __name__ == "__main__":
    main()
