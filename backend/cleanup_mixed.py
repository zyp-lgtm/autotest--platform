#!/usr/bin/env python3
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep

db = Session(engine)
try:
    db.query(UIStep).filter(UIStep.step_name.like('%混合结果%')).delete()
    db.query(UICase).filter(UICase.name.like('%混合结果%')).delete()
    db.query(UIScenario).filter(UIScenario.name.like('%混合结果%')).delete()
    task = db.query(UITask).filter(UITask.name.like('%混合结果%')).first()
    if task:
        db.delete(task)
    db.commit()
    print('✓ 已删除旧的混合结果测试任务')
finally:
    db.close()
