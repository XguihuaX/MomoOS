from faster_whisper import WhisperModel
from pydub import AudioSegment
from ..constants import ASR_MODEL_PATH
import opencc  # 👈 新增
import os


if not os.path.exists(ASR_MODEL_PATH):
    raise FileNotFoundError(f"❌ 模型目录不存在：{ASR_MODEL_PATH}")

model = WhisperModel(str(ASR_MODEL_PATH), device="cuda", compute_type="float16")

converter = opencc.OpenCC('t2s')  # 👈 繁体转简体

def recognize_audio(raw_path: str) -> str:
    fixed_path = raw_path.replace("raw_", "fixed_")

    try:
        sound = AudioSegment.from_file(raw_path)
        duration_ms = len(sound)
        print(f"[🎧] 音频时长：{duration_ms}ms")

        if duration_ms < 1000:
            print("❗音频过短，跳过识别")
            return ""

        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound.export(fixed_path, format="wav")
        print("[🎧] 音频已转换为 16kHz 单声道 PCM")

        if os.path.getsize(fixed_path) < 2048:
            print("❗音频文件太小，可能无效")
            return ""

        segments, info = model.transcribe(fixed_path, language="zh", beam_size=5, vad_filter=True)
        result = "".join([seg.text for seg in segments])

        # 👇 加上繁转简
        result = converter.convert(result)

        print("[✅] 识别结果（简体）：", result)
        os.remove(fixed_path)
        return result

    except Exception as e:
        print("[❌ 识别失败]", str(e))
        raise e
