import os
import asyncio
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
from concurrent.futures import ThreadPoolExecutor

class VideoAgent:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def create_video(self, images, audio_path, output_path="output_video.mp4", fps=24):
        if not images:
            raise ValueError("No images provided for video creation")

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print("✅ Starting video creation...")

        # ✅ Get audio duration
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration

        # ✅ Calculate duration per image
        duration_per_image = audio_duration / len(images)

        # ✅ Load and process images in parallel (async with ThreadPoolExecutor)
        print("✅ Processing images in parallel...")
        clips = await asyncio.gather(*[
            asyncio.get_event_loop().run_in_executor(self.executor, self._process_image, img, duration_per_image)
            for img in images
        ])

        # ✅ Concatenate image clips
        video_clip = concatenate_videoclips(clips, method="compose")

        # ✅ Add audio
        video_clip = video_clip.with_audio(audio_clip)

        # ✅ Write final video with ffmpeg acceleration
        print(f"✅ Rendering video: {output_path}")
        video_clip.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            threads=4,  # ✅ Multithreading
            preset="ultrafast"  # ✅ Faster render
        )

        print("🎬 Video creation complete:", output_path)

    def _process_image(self, img_path, duration):
        """Handles MoviePy version differences & resizing."""
        clip = ImageClip(img_path)

        # ✅ Handle MoviePy v2 (with_duration) vs v1 (set_duration)
        if hasattr(clip, "with_duration"):
            clip = clip.with_duration(duration)
            clip = clip.resized(width=1080)
        else:
            clip = clip.set_duration(duration)
            clip = clip.resize(width=1080)

        # ✅ Resize to 1080p width
        #clip = clip.resize(width=1080)
        return clip
