#!/usr/bin/env python3
import uuid
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep

db = Session(engine)
try:
    db.query(UIStep).delete()
    db.query(UICase).delete()
    db.query(UIScenario).delete()
    task = db.query(UITask).filter(UITask.id == uuid.UUID('190d5cd7-55a4-4649-9248-9e26de4f33f8')).first()
    if task:
        db.delete(task)
    db.commit()
    print('✓ 已清理旧任务数据')
finally:
    db.close()
