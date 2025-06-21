from ..database.model import Todo, Memory, personality, User, OwnerTypeEnum, StatusEnum, Memory_role, Memory_type,personality_type
from ..database.init import db
from ..database.scheduler import start_scheduler
from typing import Optional
from datetime import datetime

#todo_update_debouncer = Debouncer(3)
###------todo--------##
# 增：添加 todo
def add_todo(
    user_id: str,
    owner_type: OwnerTypeEnum,
    title: str,
    description: Optional[str],
    due_time: Optional[datetime],
    status: StatusEnum = StatusEnum.pending,
) -> Todo:
    try:
        todo = Todo(
            user_id=user_id,
            owner_type=owner_type,
            title=title,
            description=description,
            due_time=due_time,
            status=status,
        )
        db.session.add(todo)
        db.session.commit()
        db.session.refresh(todo)
        start_scheduler()
        return todo
    except Exception as e:
        db.session.rollback()
        raise e



# ✅ 删：根据 ID 删除 todo
def delete_todo(todo_id: int, user_id: str) -> bool:
    try:
        todo = db.session.get(Todo, todo_id)
        if not todo or todo.user_id != user_id:
            return False
        db.session.delete(todo)
        db.session.commit()
        start_scheduler()
        return True
    except Exception as e:
        db.session.rollback()
        raise e



# ✅ 删：删除所有已完成的 todo
def auto_delete_todo(user_id: str) -> bool:
    try:
        db.session.query(Todo).filter(
            Todo.user_id == user_id,
            Todo.status == StatusEnum.completed
        ).delete(synchronize_session=False)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e



# ✅ 查：根据条件筛选 todo（支持 owner_type、status、时间范围等）


def search_todo(
    user_id: str,  # ✅ 强制传入，避免越权
    id: Optional[int] = None,
    owner_type: Optional[OwnerTypeEnum] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[StatusEnum] = None,
    due_start: Optional[datetime] = None,
    due_end: Optional[datetime] = None,
    created_start: Optional[datetime] = None,
    created_end: Optional[datetime] = None,
) -> list[Todo]:
    query = db.session.query(Todo).filter(Todo.user_id == user_id)

    if id:
        query = query.filter(Todo.id == id)
    if owner_type:
        query = query.filter(Todo.owner_type == owner_type)
    if title:
        query = query.filter(Todo.title == title)
    if description:
        query = query.filter(Todo.description.like(f"%{description}%"))
    if status:
        query = query.filter(Todo.status == status)
    if due_start:
        query = query.filter(Todo.due_time >= due_start)
    if due_end:
        query = query.filter(Todo.due_time < due_end)
    if created_start:
        query = query.filter(Todo.created_at >= created_start)
    if created_end:
        query = query.filter(Todo.created_at < created_end)

    return query.order_by(Todo.due_time.asc()).all()




# ✅ 改：根据传入字段更新指定 todo
def change_todo(
    todo_id: int,
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_time: Optional[datetime] = None,
    status: Optional[StatusEnum] = None,
) -> bool:
    try:
        todo = db.session.get(Todo, todo_id)
        if not todo or todo.user_id != user_id:
            return False
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if due_time is not None:
            todo.due_time = due_time
        if status is not None:
            todo.status = status
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e



# ✅ 查：通过 ID 获取 todo（常用于 trigger_todo）。 -----------目前还没动，晚一些回来动
def get_todo_by_id(todo_id: int) -> Optional[Todo]:
    return db.session.get(Todo, todo_id)



########-------这是memory表部分---------#########
def add_memory(
    user_id: str,
    role: Memory_role,
    type: Memory_type,
    content: str,
    created_at: Optional[datetime] = None
) -> Memory:
    try:
        memory = Memory(
            user_id=user_id,
            role=role,
            type=type,
            content=content,
            created_at=created_at or datetime.now()
        )
        db.session.add(memory)
        db.session.commit()
        db.session.refresh(memory)
        return memory
    except Exception as e:
        db.session.rollback()
        raise e


# 删（按 id）
def delete_memory(memory_id: int, user_id: str) -> bool:
    try:
        memory = db.session.query(Memory).filter_by(id=memory_id, user_id=user_id).first()
        if not memory:
            return False
        db.session.delete(memory)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


# 查找记忆

def search_memory(
    user_id: str,
    role: Optional[Memory_role] = None,
    type: Optional[Memory_type] = None,
    content: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> list[Memory]:
    query = db.session.query(Memory).filter(Memory.user_id == user_id)

    if role:
        query = query.filter(Memory.role == role)
    if type:
        query = query.filter(Memory.type == type)
    if content:
        query = query.filter(Memory.content.like(f"%{content}%"))
    if start_time:
        query = query.filter(Memory.created_at >= start_time)
    if end_time:
        query = query.filter(Memory.created_at <= end_time)

    return query.order_by(Memory.created_at.desc()).all()


# 改（按 id）
def change_memory(
    memory_id: int,
    user_id: str,
    content: Optional[str] = None,
    type: Optional[Memory_type] = None
) -> bool:
    try:
        memory = db.session.query(Memory).filter_by(id=memory_id, user_id=user_id).first()
        if not memory:
            return False
        if content is not None:
            memory.content = content
        if type is not None:
            memory.type = type
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e



# ✅ personality

# 增（有则更新）
def add_personality(
    user_id: str,
    type: personality_type,
    tag: str,
    content: str
) -> None:
    try:
        record = db.session.query(personality).filter_by(
            user_id=user_id,
            type=type,
            tag=tag
        ).first()
        if record:
            record.content = content
        else:
            record = personality(
                user_id=user_id,
                type=type,
                tag=tag,
                content=content
            )
            db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


# 查
def search_personality(user_id: str, type: Optional[personality_type] = None, tag: Optional[str] = None) -> list[personality]:
    query = db.session.query(personality).filter_by(user_id=user_id)
    if type:
        query = query.filter_by(type=type)
    if tag:
        query = query.filter_by(tag=tag)
    return query.all()

# 删
def delete_personality(user_id: str, type: personality_type, tag: str) -> bool:
    try:
        record = db.session.query(personality_type).filter_by(user_id=user_id, type=type, tag=tag).first()
        if not record:
            return False
        db.session.delete(record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e

# 改
def change_personality(user_id: str, type: personality_type, tag: str, content: str) -> bool:
    try:
        record = db.session.query(personality_type).filter_by(user_id=user_id, type=type, tag=tag).first()
        if not record:
            return False
        record.content = content # type: ignore
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e



#-----user--------------#
def add_user(user_id: str) -> bool:
    try:
        exists = db.session.query(User).filter_by(user_id=user_id).first()
        if exists:
            return False  # 已存在
        user = User(user_id=user_id)
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def get_user_by_id(user_id: str) -> Optional[User]:
    return db.session.query(User).filter_by(user_id=user_id).first()


def get_all_users() -> list[User]:
    return db.session.query(User).order_by(User.created_at.desc()).all()



def delete_user(user_id: str) -> bool:
    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def get_all_user_ids_from_memory():
    try:
        results = db.session.query(Memory.user_id).distinct().all()
        return [r[0] for r in results]
    except Exception as e:
        print(f"[memory_service] 获取所有 user_id 失败: {e}")
        return []


