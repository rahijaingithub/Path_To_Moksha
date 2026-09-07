import os
import wave
import math
import struct

SFX_DIR = "assets/audio/sfx"
BGM_DIR = "assets/audio/bgm"
os.makedirs(SFX_DIR, exist_ok=True)
os.makedirs(BGM_DIR, exist_ok=True)

SAMPLE_RATE = 44100

def save_wav(filename, samples):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        # Convert float samples (-1.0 to 1.0) to 16-bit PCM
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            wav_file.writeframesraw(struct.pack('<h', int(clamped * 32767)))

# 1. Jump (short upward sweep)
samples = []
for i in range(int(SAMPLE_RATE * 0.15)):
    t = i / SAMPLE_RATE
    freq = 400 + 800 * (t / 0.15)
    env = 1.0 - (t / 0.15)
    samples.append(0.5 * env * math.sin(2 * math.pi * freq * t))
save_wav(os.path.join(SFX_DIR, "jump.wav"), samples)

# 2. Box Open (chime)
samples = []
for i in range(int(SAMPLE_RATE * 0.3)):
    t = i / SAMPLE_RATE
    freq1, freq2 = 800, 1200
    env = math.exp(-t * 10)
    val = (math.sin(2 * math.pi * freq1 * t) + math.sin(2 * math.pi * freq2 * t)) / 2.0
    samples.append(0.5 * env * val)
save_wav(os.path.join(SFX_DIR, "box_open.wav"), samples)

# 3. Correct (harmonious chord)
samples = []
for i in range(int(SAMPLE_RATE * 0.5)):
    t = i / SAMPLE_RATE
    # C major chord (C E G)
    val = (math.sin(2 * math.pi * 523.25 * t) + 
           math.sin(2 * math.pi * 659.25 * t) + 
           math.sin(2 * math.pi * 783.99 * t)) / 3.0
    env = math.exp(-t * 5)
    samples.append(0.5 * env * val)
save_wav(os.path.join(SFX_DIR, "correct.wav"), samples)

# 4. Wrong (low buzzer)
samples = []
for i in range(int(SAMPLE_RATE * 0.4)):
    t = i / SAMPLE_RATE
    freq = 150
    # Square wave approx
    val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
    env = math.exp(-t * 4)
    samples.append(0.3 * env * val)
save_wav(os.path.join(SFX_DIR, "wrong.wav"), samples)

# 5. Hazard (static/splash)
import random
samples = []
for i in range(int(SAMPLE_RATE * 0.3)):
    t = i / SAMPLE_RATE
    env = math.exp(-t * 15)
    samples.append(0.4 * env * random.uniform(-1.0, 1.0))
save_wav(os.path.join(SFX_DIR, "hazard.wav"), samples)

# 6. Level Complete (ascending arpeggio)
samples = []
notes = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
duration = 1.5
for i in range(int(SAMPLE_RATE * duration)):
    t = i / SAMPLE_RATE
    note_idx = min(len(notes) - 1, int(t / (duration / len(notes))))
    freq = notes[note_idx]
    env = math.exp(-(t % (duration / len(notes))) * 10)
    samples.append(0.5 * env * math.sin(2 * math.pi * freq * t))
save_wav(os.path.join(SFX_DIR, "level_complete.wav"), samples)

# 7. BGM (calm rhythmic drone)
samples = []
duration = 8.0 # 8 second loop
for i in range(int(SAMPLE_RATE * duration)):
    t = i / SAMPLE_RATE
    # Base drone
    val = math.sin(2 * math.pi * 130.81 * t) # C3
    # Slow pulse
    pulse = (1 + math.sin(2 * math.pi * 0.5 * t)) / 2.0
    samples.append(0.2 * val * pulse)
save_wav(os.path.join(BGM_DIR, "bgm_loop.wav"), samples)

print("Audio files generated successfully!")
