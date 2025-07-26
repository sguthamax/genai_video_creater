import os
import asyncio
import aiofiles
from pathlib import Path
from typing import List
from pydub import AudioSegment
from openai import AsyncOpenAI
from gtts import gTTS
import tempfile
import logging

logger = logging.getLogger(__name__)

class AudioAgent:
    def __init__(self, output_dir="output/audio"):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize_text_to_speech_openai(self, text: str, output_file: Path):
        """Generate audio using OpenAI TTS API."""
        try:
            response = await self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text
            )
            async with aiofiles.open(output_file, "wb") as f:
                await f.write(await response.aread())
            logger.info(f"✅ OpenAI TTS audio saved: {output_file}")
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise

    async def synthesize_text_to_speech_gtts(self, text: str, output_file: Path):
        """Fallback to gTTS if OpenAI fails."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._gtts_sync, text, output_file)
            logger.info(f"✅ gTTS audio saved: {output_file}")
        except Exception as e:
            logger.error(f"gTTS failed: {e}")
            raise

    def _gtts_sync(self, text: str, output_file: Path):
        """Blocking gTTS call in a separate thread."""
        tts = gTTS(text=text, lang="en")
        tts.save(str(output_file))

    async def generate_audio(self, script: str) -> str:
        """Split script into chunks, generate audio in parallel, combine them."""
        if not script or not script.strip():
            raise ValueError("Script is empty!")

        # Split into chunks (~400 chars)
        chunks = [script[i:i + 400] for i in range(0, len(script), 400)]
        audio_files: List[Path] = []

        for i, chunk in enumerate(chunks):
            output_file = self.output_dir / f"chunk_{i}.mp3"
            try:
                await self.synthesize_text_to_speech_openai(chunk, output_file)
            except Exception:
                logger.warning("⚠ Falling back to gTTS...")
                await self.synthesize_text_to_speech_gtts(chunk, output_file)
            audio_files.append(output_file)

        # Combine audio chunks
        combined_audio = AudioSegment.empty()
        for file in audio_files:
            combined_audio += AudioSegment.from_mp3(file)

        final_path = self.output_dir / "final_audio.mp3"
        combined_audio.export(final_path, format="mp3")
        logger.info(f"✅ Combined audio saved: {final_path}")
        return str(final_path)
