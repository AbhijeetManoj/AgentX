import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
from fastapi.responses import StreamingResponse
import json
import uuid
import db

# Import our agent from app
from app import agent, system_prompt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    prompt: str

class UpdateNameRequest(BaseModel):
    name: str

@app.get("/api/dag")
def get_dag():
    try:
        mermaid_str = agent.get_graph().draw_mermaid()
        return {"mermaid": mermaid_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
def run_agent(req: RunRequest):
    # stream response 
    def event_stream():
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dynamic_system_prompt = f"{system_prompt}\n\nCurrent Date and Time: {current_time_str}\nTimezone: Asia/Kolkata (IST)"
        messages = [
            ("system", dynamic_system_prompt),
            ("user", req.prompt)
        ]

        full_message_log = []
        graph_events = []

        try:
            # We use stream to get step-by-step execution 
            for chunk in agent.stream({"messages": messages}):
                # chunk is a dict with node name as key (e.g. 'agent', 'tools')
                for node_name, value in chunk.items():
                    if 'messages' in value and value['messages']:
                        # get the last message
                        last_message = value['messages'][-1]
                        
                        event_data = {
                            "node": node_name,
                            "type": last_message.type,
                            "content": last_message.content if hasattr(last_message, 'content') else str(last_message)
                        }
                        
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            event_data["tool_calls"] = last_message.tool_calls
                            
                        # Keep track to store in DB
                        full_message_log.append(event_data)
                        if "tool_calls" in event_data:
                             graph_events.extend(event_data["tool_calls"])
                             
                        yield f"data: {json.dumps(event_data)}\n\n"
                        
            # Save the successful run locally
            db.save_workflow_run(req.prompt, {"executed_tools": graph_events}, full_message_log)
            yield "data: {\"done\": true}\n\n"
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/history")
def get_history():
    return db.get_workflow_runs()
    
@app.get("/api/history/{run_id}")
def get_history_detail(run_id: int):
    run = db.get_workflow_by_id(run_id)
    if not run:
         raise HTTPException(status_code=404, detail="Run not found")
    return {
         "id": run.id,
         "name": run.name,
         "prompt": run.prompt,
         "graph_data": json.loads(run.graph_data_json),
         "messages": json.loads(run.messages_json),
         "created_at": str(run.created_at)
    }

@app.patch("/api/history/{run_id}/name")
def update_workflow_name(run_id: int, req: UpdateNameRequest):
    success = db.update_workflow_name(run_id, req.name)
    if not success:
         raise HTTPException(status_code=400, detail="Failed to update name. Run may not exist.")
    return {"status": "success"}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
