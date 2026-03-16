import gradio as gr
import os
import json
from datetime import datetime
from pathlib import Path
from itertools import count
from threading import Lock

#from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from models.room_state import RoomStateManager
from models.room_relationship import RoomRelationshipManager
from models.room_graph import RoomGraphVisualizer
from models.phase_tracker import DesignPhaseTracker
from models.room_state_llm import RoomStateLLM
from models.room_relationship_llm import RoomRelationshipLLM
from managers.memory import CustomSummaryMemory
from managers.phase_transition import PhaseTransitionLLM
from utils.constants import system_message, room_id

LOG_PATH = Path(__file__).resolve().parent / "chat_logs.jsonl"
CHAT_ID_COUNTER = count(1)
CHAT_ID_LOCK = Lock()

def _next_chat_id():
    with CHAT_ID_LOCK:
        return next(CHAT_ID_COUNTER)


def _log_chat_entry(role, content, phase_name):
    entry = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "role": role,
        "content": content,
        "phase": phase_name,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Initialize API key and base URL
api_key = ""
base_url = ""

# Initialize the chat model
# model = init_chat_model("gpt-4o", api_key=api_key, base_url=base_url)
model = ChatOpenAI(model="gpt-4o", api_key=api_key, base_url=base_url) # type: ignore

# Initialize managers
room_tool = RoomStateManager()
relationship_tool = RoomRelationshipManager(room_tool)
phase_tracker = DesignPhaseTracker()

# Initialize LLM components
room_state_llm = RoomStateLLM(room_tool, model)
relationship_llm = RoomRelationshipLLM(relationship_tool, model)
phase_transition_llm = PhaseTransitionLLM(model, room_state_llm, relationship_llm)

# Initialize memory
memory = CustomSummaryMemory(
    system=system_message,
    llm=model,
    max_tokens=2000,
    room_state_llm=room_state_llm,
    relationship_llm=relationship_llm
)

def process(message, history):
    # Add user message to memory
    message = message.get("text", "")
    memory.add_user_message(message)
    _log_chat_entry("user", message, phase_tracker.get_phase_name())
    response = model.invoke(memory.buffer)
    memory.add_ai_message(response.content)
    
    # Check if we should transition to next phase
    transition_decision = phase_transition_llm.should_transition(
        phase_tracker.get_current_phase(),
        f"User: {message}\nAI: {response.content}"
    )
    
    # If transitioning, update phase
    if transition_decision["should_transition"]:
        phase_tracker.move_to_next_phase()
        # Add missing elements note if any
        if transition_decision["missing_elements"]:
            response.content += "\n\nNote: " + ", ".join(transition_decision["missing_elements"])
    
    # Get current phase (may be updated)
    current_phase = phase_tracker.get_current_phase()
    
    # Process based on current phase
    if current_phase == 1:
        # Phase 1: Update room state
        room_state_llm.process_conversation(f"User: {message}\nAI: {response.content}")
        visualization = None
    
    elif current_phase == 2:
        # Phase 2: Update room relationships
        relationship_results, visualization = relationship_llm.process_conversation(f"User: {message}\nAI: {response.content}")
    
    elif current_phase == 3:
        # Phase 3: Generate layout info
        layout_info = relationship_tool.get_room_layout_info(room_tool)
        response.content = "Generating layout diagram..."
        visualization = None
    
    # Build result
    result = []
    result.append(response.content)
    result.append(f"Current Phase: {phase_tracker.get_phase_name()}")
    
    if current_phase == 3:
        result.append(f"Layout Info: {layout_info}")
    
    if current_phase == 2 and visualization is not None:
        result.append(gr.Image(visualization))

    _log_chat_entry("assistant", response.content, phase_tracker.get_phase_name())
    
    return result

# Create and launch the Gradio interface
demo = gr.ChatInterface(
    title="Floor Plan Designer",
    fn=process, 
    multimodal=True,
    type="messages",
    description="This is a floor plan designer. You can use it to design your floor plan. You can also use it to ask questions about the floor plan.",
)

if __name__ == "__main__":
    #demo.launch(share=True)
    demo.launch() 
