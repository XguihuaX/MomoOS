from datetime import datetime,timedelta
from threading import Timer

from database.model import OwnerTypeEnum, StatusEnum


def scan_pending_todos():
    from database.services import search_todo
    print("scheduler:正在重新扫描当日日程")
    now = datetime.now()
    tomorrow_start = datetime(now.year, now.month, now.day) + timedelta(days=1)

    # 查询所有未完成的待办事项（alarm/schedule）
    todos = search_todo(
        owner_type=None,
        status=StatusEnum.pending,
        due_start = now,
        due_end = tomorrow_start
    )
    print("scheduler:当日日程有")
    valid_todos = []
    for todo in todos:
        if todo.owner_type not in [OwnerTypeEnum.alarm, OwnerTypeEnum.schedule]:
            continue
        valid_todos.append(todo)

    return valid_todos


def register_todo_timer(todo):
    now = datetime.now()
    delay = (todo.due_time - now).total_seconds()
    print(f"[⏰ 注册定时器] 任务：{todo.title} | delay={delay:.1f}s")
    if delay > 0:
        Timer(delay, trigger_todo, args=[todo.id]).start()
        print(f"[调度注册] {todo.title} 将在 {todo.due_time} 执行")
    else:
        print(f"[补发执行] {todo.id} 的 {todo.description} 时间已过（{todo.due_time}），立即触发")
        trigger_todo(todo.id)


def start_scheduler():
    todos = scan_pending_todos()
    for todo in todos:
        register_todo_timer(todo)




def trigger_todo(todo_id: int):
    from app import app  # 💡 确保 app 可导入（避免循环 import）
    with app.app_context():  # ✅ 显式包一层
        from database.services import change_todo, search_todo
        import base64, tempfile, requests, subprocess

        todos = search_todo(id=todo_id)
        if not todos:
            return

        todo = todos[0]
        if todo.status not in [StatusEnum.pending, StatusEnum.multiple]:
            return

        change_todo(todo_id, status=StatusEnum.completed)

        try:
            tts_response = requests.post("http://127.0.0.1:5001/api/tts", json={
                "text": todo.description,
                "emotion": "八重神子默认"
            })

            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                print("[🔔 闹钟语音提醒]:", tts_data.get("text"))

                audio_base64 = tts_data.get("audio")
                if audio_base64:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(base64.b64decode(audio_base64))
                        f.flush()
                        subprocess.run(["afplay", f.name])  # 播放音频
            else:
                print("[⚠️ TTS请求失败]:", tts_response.text)

        except Exception as e:
            print(f"[❌ 闹钟 TTS 播放失败]: {e}")
