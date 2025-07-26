import os
import asyncio
from langgraph.graph import StateGraph, END
from typing import TypedDict

from agents.script_agent import ScriptAgent
from agents.audio_agent import AudioAgent
from agents.video_agent import VideoAgent

# ✅ Define State Schema
class VideoState(TypedDict):
    text: str
    images: list[str]
    script: str
    audio_path: str
    video_path: str

# ✅ Initialize Agents
script_agent = ScriptAgent()
audio_agent = AudioAgent()
video_agent = VideoAgent()

# ✅ Create Workflow
def create_video_workflow():
    workflow = StateGraph(VideoState)

    # ---- Node 1: Script Generation ----
    async def generate_script(state: VideoState):
        response = await script_agent.generate_script(state["text"])

        # Normalize script to string
        if hasattr(response, "content"):  # AIMessage or similar
            script_text = response.content
        elif isinstance(response, str):
            script_text = response
        else:
            script_text = str(response)

        if not script_text.strip():
            raise ValueError("Generated script is empty!")

        state["script"] = script_text
        return state

    workflow.add_node("generate_script", generate_script)

    # ---- Node 2: Audio Generation ----
    async def generate_audio(state: VideoState):
        audio_path = await audio_agent.generate_audio(state["script"])
        state["audio_path"] = audio_path
        return state

    workflow.add_node("generate_audio", generate_audio)

    # ---- Node 3: Video Creation ----
    async def create_video(state: VideoState):
        output_path = state["video_path"]
        await video_agent.create_video(
            images=state["images"],
            audio_path=state["audio_path"],
            output_path=output_path
        )

        # ✅ Cleanup temporary files
        try:
            for img in state["images"]:
                if os.path.exists(img):
                    os.remove(img)
            if os.path.exists(state["audio_path"]):
                os.remove(state["audio_path"])
        except Exception as e:
            print(f"Cleanup error: {e}")

        return state

    workflow.add_node("create_video", create_video)

    # ✅ Define Edges
    workflow.add_edge("generate_script", "generate_audio")
    workflow.add_edge("generate_audio", "create_video")
    workflow.add_edge("create_video", END)

    # ✅ Set Entry Point
    workflow.set_entry_point("generate_script")

    return workflow.compile()

# ✅ Main function to run the pipeline
async def generate_video(text: str, images: list[str], output_path: str):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    app = create_video_workflow()

    initial_state: VideoState = {
        "text": text,
        "images": images,
        "script": "",
        "audio_path": "",
        "video_path": output_path
    }

    await app.ainvoke(initial_state)
