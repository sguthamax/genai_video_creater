from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os


class ScriptAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    async def generate_script(self, text: str) -> str:
        prompt = f"Create a detailed video narration script based on this text:\n{text}"
        response = await self.llm.ainvoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
