import requests
import os
import subprocess
from pathlib import Path
from pydub import AudioSegment

REMOTE_API = "http://117.50.190.72:8000/infer_single"
SAVE_DIR = "../../audio"
os.makedirs(SAVE_DIR, exist_ok=True)
def normalize_wav(path: str):
    try:
        audio = AudioSegment.from_file(path)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(path, format="wav")
        print(f"[🎧] 音频格式标准化完成：{path}")
    except Exception as e:
        print(f"[⚠️] 音频标准化失败：{e}")


def generate_audio(
    text: str,
    model_name: str,
    emotion: str = "默认",
    lang: str = "中文",
    play: bool = True
) -> str:
    if not text.strip():
        raise ValueError("文本不能为空！")

    payload = {
        "version": "v4",
        "model_name": model_name,
        "emotion": emotion,
        "text": text,
        "text_lang": lang,
        "prompt_text_lang": "中文"
    }

    print("[📤] 请求 payload：", payload)
    response = requests.post(REMOTE_API, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"语音合成失败，状态码：{response.status_code}")

    result = response.json()
    print("[🌐] 接口完整返回内容：", result)
    audio_url = result.get("audio_url")
    if audio_url and audio_url.startswith("http://0.0.0.0"):
        audio_url = audio_url.replace("0.0.0.0", "117.50.190.72")

    if not audio_url:
        raise RuntimeError("接口未返回有效 audio_url")

    audio_response = requests.get(audio_url)
    if audio_response.status_code != 200:
        raise RuntimeError(f"音频下载失败：{audio_response.status_code}")

    # 用 model_name 作为保存文件名，避免重复角色名混淆
    sanitized_name = model_name.replace("/", "_")
    output_path = os.path.join(SAVE_DIR, f"output_{sanitized_name}.wav")
    with open(output_path, "wb") as f:
        f.write(audio_response.content)

    normalize_wav(output_path)
    print(f"[✅] 合成完成，保存路径：{output_path}")


    return output_path



