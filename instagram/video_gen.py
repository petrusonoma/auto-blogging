import subprocess
import os
from pathlib import Path

# Output dimensions — Instagram Reels standard
WIDTH = 1080
HEIGHT = 1920
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"  # fallback serif


def _escape(text: str) -> str:
    """Escape special characters for ffmpeg drawtext filter."""
    return (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]")
    )


def build_video(scenes: list[dict], image_paths: list[str], output_path: str, music_path: str = None) -> str:
    """
    scenes: list of {"duration": int, "overlay_text": str}
    image_paths: list of local image file paths (same length or longer than scenes)
    output_path: path for the final MP4
    music_path: optional path to background music file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Build per-scene clips with Ken Burns + text overlay ---
    clip_paths = []
    for i, scene in enumerate(scenes):
        img = image_paths[i % len(image_paths)]
        duration = scene.get("duration", 4)
        text = _escape(scene.get("overlay_text", ""))
        clip_out = f"/tmp/clip_{i:02d}.mp4"

        # Ken Burns: slow zoom-in, recentered
        zoom_expr = f"min(zoom+0.0015,1.3)"
        total_frames = duration * 25  # 25 fps

        vf_parts = [
            # Scale up to allow zoom movement
            f"scale=2*{WIDTH}:2*{HEIGHT},",
            # Ken Burns zoompan
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s={WIDTH}x{HEIGHT}:fps=25,",
            # Slight vignette for luxury feel
            f"vignette=PI/4,",
        ]

        # Text overlay — bottom third, serif, soft white
        if text:
            # Word-wrap: max 4 words per line
            words = text.split()
            lines = []
            for i in range(0, len(words), 4):
                lines.append(" ".join(words[i:i+4]))
            wrapped = "\n".join(lines)
            wrapped = _escape(wrapped)

            vf_parts.append(
                f"drawtext=fontfile={FONT_PATH}"
                f":text='{wrapped}'"
                f":fontcolor=white@0.88"
                f":fontsize=52"
                f":x=(w-text_w)/2"
                f":y=h*0.75"
                f":shadowcolor=black@0.6"
                f":shadowx=2:shadowy=2"
                f":line_spacing=10"
                f":fix_bounds=true"
            )

        vf = "".join(vf_parts)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "25",
            clip_out,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        clip_paths.append(clip_out)
        print(f"  ✓ Scene {i+1} rendered")

    # --- Step 2: Concatenate all clips + mix music ---
    concat_list = "/tmp/concat_list.txt"
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")

    total_duration = sum(s.get("duration", 4) for s in scenes)

    if music_path:
        # Fade out music in last 2 seconds
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume=0.5,afade=t=out:st={total_duration-2}:d=2[music]",
            "-map", "0:v",
            "-map", "[music]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
    else:
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

    subprocess.run(cmd_concat, check=True, capture_output=True)
    print(f"  ✓ Final video: {output_path}")

    # Cleanup
    for cp in clip_paths:
        os.remove(cp)

    return output_path


if __name__ == "__main__":
    # Quick test with placeholder
    test_scenes = [
        {"duration": 4, "overlay_text": "some things are made to last"},
        {"duration": 4, "overlay_text": "craft over convenience"},
        {"duration": 4, "overlay_text": "the rest is noise"},
    ]
    # Requires real image paths
    print("video_gen.py ready — run via publish_reels.py")
