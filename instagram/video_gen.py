import subprocess
import os
from pathlib import Path

WIDTH = 1080
HEIGHT = 1920
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]")
    )


def _match_image(hint: str, image_paths: list[str], fallback_index: int) -> str:
    """Match image by filename keywords from visual_hint. Falls back to index-based."""
    if not hint:
        return image_paths[fallback_index % len(image_paths)]

    hint_words = set(hint.lower().replace("_", " ").replace("-", " ").split())
    best_path = None
    best_score = 0

    for path in image_paths:
        filename = Path(path).stem.lower().replace("_", " ").replace("-", " ")
        file_words = set(filename.split())
        score = len(hint_words & file_words)
        if score > best_score:
            best_score = score
            best_path = path

    if best_path and best_score > 0:
        return best_path

    return image_paths[fallback_index % len(image_paths)]


def build_video(scenes: list[dict], image_paths: list[str], output_path: str, music_path: str = None) -> str:
    """
    scenes: list of {"duration": int, "overlay_text": str, "visual_hint": str}
    image_paths: list of local image file paths
    output_path: path for the final MP4
    music_path: optional path to background music file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 3 Ken Burns effect patterns — cycle through scenes
    KB_EFFECTS = [
        lambda f: f"zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={f}:s={WIDTH}x{HEIGHT}:fps=25",
        lambda f: f"zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.002))':x='iw/2-(iw/zoom/2)+20*on/{f}':y='ih/2-(ih/zoom/2)':d={f}:s={WIDTH}x{HEIGHT}:fps=25",
        lambda f: f"zoompan=z='min(zoom+0.001,1.25)':x='iw/2-(iw/zoom/2)':y='ih-(ih/zoom)-((ih-(ih/zoom))*on/{f})':d={f}:s={WIDTH}x{HEIGHT}:fps=25",
    ]

    clip_paths = []
    for i, scene in enumerate(scenes):
        hint = scene.get("visual_hint", "")
        img = _match_image(hint, image_paths, i)
        if hint:
            print(f"  Scene {i+1} image: {Path(img).name} (hint: '{hint[:30]}')")

        duration = scene.get("duration", 4)
        text = _escape(scene.get("overlay_text", ""))
        clip_out = f"/tmp/clip_{i:02d}.mp4"

        total_frames = duration * 25
        kb_effect = KB_EFFECTS[i % len(KB_EFFECTS)](total_frames)

        vf_parts = [
            f"scale={WIDTH*2}:{HEIGHT*2}:force_original_aspect_ratio=increase,",
            f"crop={WIDTH*2}:{HEIGHT*2},",
            f"{kb_effect},",
            f"vignette=PI/4,",
        ]

        if text:
            words = text.split()
            lines = []
            for j in range(0, len(words), 4):
                lines.append(" ".join(words[j:j+4]))
            wrapped = _escape("\n".join(lines))

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
        print(f"  ✓ Scene {i+1} rendered")
        clip_paths.append(clip_out)

    # Concatenate all clips + mix music
    concat_list = "/tmp/concat_list.txt"
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")

    total_duration = sum(s.get("duration", 4) for s in scenes)

    if music_path:
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

    for cp in clip_paths:
        os.remove(cp)

    return output_path


if __name__ == "__main__":
    print("video_gen.py ready — run via publish_reels.py")
