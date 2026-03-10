from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import json

DATABASE_URL = "sqlite:///./workflows.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True) # Custom workflow name
    prompt = Column(String, index=True)
    graph_data_json = Column(Text) # Store nodes/edges to regenerate past runs
    messages_json = Column(Text) # Store chat history log
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def save_workflow_run(prompt: str, graph_data: dict, messages: list):
    db = SessionLocal()
    try:
        log = WorkflowLog(
            prompt=prompt,
            graph_data_json=json.dumps(graph_data),
            messages_json=json.dumps(messages)
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log.id
    except Exception as e:
        print(f"DB Error: {e}")
        db.rollback()
    finally:
        db.close()

def get_workflow_runs():
    db = SessionLocal()
    try:
        logs = db.query(WorkflowLog).order_by(WorkflowLog.created_at.desc()).limit(20).all()
        return [{"id": l.id, "name": l.name, "prompt": l.prompt, "created_at": str(l.created_at)} for l in logs]
    finally:
        db.close()
        
def get_workflow_by_id(run_id: int):
    db = SessionLocal()
    try:
        return db.query(WorkflowLog).filter(WorkflowLog.id == run_id).first()
    finally:
        db.close()

def update_workflow_name(run_id: int, new_name: str):
    db = SessionLocal()
    try:
        log = db.query(WorkflowLog).filter(WorkflowLog.id == run_id).first()
        if log:
            log.name = new_name
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"DB Update Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()
