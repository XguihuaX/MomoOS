import requests
import os
import subprocess
from pydub import AudioSegment
from pathlib import Path

SOVITS_API = "http://127.0.0.1:9880/"
SAVE_DIR = "../../audio"
os.makedirs(SAVE_DIR, exist_ok=True)


def get_reference_audio_path(rel_path: str) -> str:
    """
    根据给定的相对路径构造参考音频的绝对路径。
    明确 base 路径，避免 __file__ 带来的问题。
    """
    base_dir = Path("/workspace/ai_project/tts_model")  # ✅ 显式指定 base 路径
    full_path = base_dir / Path(rel_path)
    return str(full_path.resolve())

VOICE_PRESETS = {
    "八重神子默认": {
        "refer_wav_path": get_reference_audio_path("v4/八重神子_ZH/reference_audios/中文/emotions/【默认】嗨，小家伙们，你们来了呀。不错，很准时。.wav"),
        "prompt_text": "嗨，小家伙们，你们来了呀。不错，很准时。",
        "prompt_language": "zh"
    },
    "凝光默认": {
        "refer_wav_path": get_reference_audio_path(
            "/Users/liujunhong/Desktop/program/model/v4/凝光_ZH/reference_audios/中文/emotions/【默认】我打算新做一套棋盘和棋子，内容就从前段时间的那场大战改编而来。.wav"),
        "prompt_text": "我打算新做一套棋盘和棋子，内容就从前段时间的那场大战改编而来。",
        "prompt_language": "zh"
    },
    "神里绫华默认": {
        "refer_wav_path": get_reference_audio_path(
            "v4/神里绫华_ZH/reference_audios/中文/emotions/【默认】看来，你们能理解我的心情了，既然这样，不知能否再考虑一下….wav"),
        "prompt_text": "看来，你们能理解我的心情了，既然这样，不知能否再考虑一下…",
        "prompt_language": "zh"
    },
    "荧默认": {
        "refer_wav_path": get_reference_audio_path("v4/荧_ZH/reference_audios/中文/emotions/【默认】是那种情况吧，时间的流动在同一天不断循环着。.wav"),
        "prompt_text": "是那种情况吧，时间的流动在同一天不断循环着。",
        "prompt_language": "zh"
    },
}

def normalize_wav(path: str):
    try:
        audio = AudioSegment.from_file(path)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(path, format="wav")
        print(f"[🎧] 音频格式标准化完成：{path}")
    except Exception as e:
        print(f"[⚠️] 音频标准化失败：{e}")

def play_audio(path: str):
    try:
        subprocess.run(["afplay", path])
    except Exception as e:
        print(f"[⚠️] 播放失败：{e}")

def generate_audio(text: str, emotion: str = "八重神子默认", filename: str = "output") -> str:
    if not text.strip():
        raise ValueError("文本不能为空！")

    if emotion not in VOICE_PRESETS:
        raise ValueError(f"未知的情绪标签：{emotion}")

    preset = VOICE_PRESETS[emotion]
    payload = {
        **preset,
        "text": text,
        "text_language": "zh",
        "cut_punc": "，。",
        "top_k": 20,
        "top_p": 0.7,
        "temperature": 0.8,
        "speed": 1.0,
        "sample_steps": 32,
        "if_sr": False,
        "language": "zh",
        "style": "neutral",
        "sdp_ratio": 0.2,
    }

    response = requests.post(SOVITS_API, json=payload, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"语音合成失败，状态码：{response.status_code}")

    if filename.endswith(".wav") or filename.startswith("/"):
        output_path = filename
    else:
        output_path = os.path.join(SAVE_DIR, f"{filename}_{emotion}.wav")

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    normalize_wav(output_path)
    print(f"[✅] 合成完成，保存路径：{output_path}")

    play_audio(output_path)  # ✅ 自动播放
    return output_path

