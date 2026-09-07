import subprocess
import os

def extract_and_fade_audio(
    input_file: str,
    output_file: str,
    start_time: int = 40,
    duration: int = 30,
    fade_in_duration: float = 0.5,
    fade_out_start: int = 28,
    fade_out_duration: float = 2,
    bitrate: str = "320k"
) -> bool:
    """
    Extract audio segment and apply fade in/out effects.
    
    Args:
        input_file: Path to input MP3
        output_file: Path to output MP3
        start_time: Start position in seconds (default: 40)
        duration: Segment duration in seconds (default: 30)
        fade_in_duration: Fade-in duration in seconds (default: 0.5)
        fade_out_start: Fade-out start time in seconds (default: 28)
        fade_out_duration: Fade-out duration in seconds (default: 2)
        bitrate: Output bitrate (default: 320k)
    
    Returns:
        True if successful, False otherwise
    """
    
    # Build the ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-ss", str(start_time),
        "-t", str(duration),
        "-af", f"afade=t=in:st=0:d={fade_in_duration},afade=t=out:st={fade_out_start}:d={fade_out_duration}",
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", bitrate,
        output_file
    ]
    
    try:
        print(f"Processing: {input_file}")
        print(f"Extracting {duration}s from {start_time}s mark...")
        
        # Execute ffmpeg
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print(f"✓ Successfully created: {output_file}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"✗ FFmpeg error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ FFmpeg not found. Install with: sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (Mac)")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    input_audio = r"D:\Jain_game_workspace\Music and Videos\high_impact_arcticfoxmusic.mp3"
    output_audio =  r"D:\Jain_game_workspace\Music and Videos\Path_to_Moksha_Teaser_Music_30s.mp3"
    
    if os.path.exists(input_audio):
        extract_and_fade_audio(input_audio, output_audio)
    else:
        print(f"Input file not found: {input_audio}")