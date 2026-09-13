# Project: Local AI Voice Studio — IndexTTS 2.5

Build a complete, polished, production-quality **local web-based AI Voice Studio** powered primarily by **IndexTTS 2.5**.

The application will run locally on a Windows PC and provide a modern browser-based interface for:

* zero-shot voice cloning
* text-to-speech
* advanced emotion control
* emotion mixing
* natural-language emotion prompting
* emotion-reference audio
* speaker/reference management
* speech speed control
* multiple takes/variations
* audio enhancement
* noise reduction
* normalization
* waveform editing
* trimming/cutting
* silence removal
* fades
* loudness control
* project/history management
* presets
* batch generation
* WAV/MP3/FLAC export

The target machine is:

```text
OS: Windows 11
GPU: NVIDIA RTX 5060 Ti 16 GB
CPU: modern desktop CPU
RAM: assume 32 GB where available
Browser: Chrome / Edge
```

Everything should run **locally**.

Do NOT require a cloud TTS API.

The application should feel like a lightweight combination of:

```text
ElevenLabs
+
Audacity
+
AI Voice Cloning Studio
+
Emotion Editor
```

but running locally with IndexTTS 2.5.

---

# 1. Core Architecture

Use this architecture:

```text
Browser UI
    ↓
React / TypeScript
    ↓
REST + WebSocket API
    ↓
FastAPI
    ↓
Voice Generation Service
    ↓
IndexTTS 2.5
    ↓
Audio Processing Pipeline
    ↓
Generated Audio
```

Recommended stack:

## Frontend

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
Lucide icons
WaveSurfer.js
Zustand
TanStack Query
```

## Backend

```text
Python 3.10/3.11
FastAPI
Uvicorn
Pydantic
PyTorch
IndexTTS 2.5
soundfile
numpy
scipy
librosa
FFmpeg
```

Optional:

```text
DeepFilterNet
RNNoise
Silero VAD
pyloudnorm
```

Do not use Gradio for the main application.

A small developer/debug Gradio interface is acceptable, but the actual application must use React + FastAPI.

---

# 2. Project Structure

Use a modular architecture approximately like:

```text
voice-studio/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── generation.py
│   │   ├── voices.py
│   │   ├── projects.py
│   │   ├── audio.py
│   │   ├── enhancement.py
│   │   ├── presets.py
│   │   ├── system.py
│   │   └── websocket.py
│   │
│   ├── tts/
│   │   ├── engine.py
│   │   ├── indextts_engine.py
│   │   ├── model_manager.py
│   │   ├── emotion.py
│   │   ├── text_processor.py
│   │   ├── language.py
│   │   └── generation_queue.py
│   │
│   ├── audio/
│   │   ├── processor.py
│   │   ├── enhancer.py
│   │   ├── denoise.py
│   │   ├── normalize.py
│   │   ├── silence.py
│   │   ├── equalizer.py
│   │   ├── compressor.py
│   │   ├── limiter.py
│   │   ├── waveform.py
│   │   ├── converter.py
│   │   └── editor.py
│   │
│   ├── services/
│   │   ├── project_service.py
│   │   ├── voice_service.py
│   │   ├── history_service.py
│   │   ├── preset_service.py
│   │   ├── export_service.py
│   │   └── file_service.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── utils/
│   │   ├── gpu.py
│   │   ├── paths.py
│   │   ├── logging.py
│   │   └── validation.py
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── stores/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── types/
│   │   └── utils/
│   │
│   └── package.json
│
├── data/
│   ├── voices/
│   ├── projects/
│   ├── generations/
│   ├── exports/
│   ├── presets/
│   └── temp/
│
├── checkpoints/
├── scripts/
│   ├── install.ps1
│   ├── download_models.py
│   ├── start.ps1
│   └── diagnose.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 3. IndexTTS 2.5 Integration

Use the official IndexTTS repository and IndexTTS 2.5 inference implementation.

Initialize approximately:

```python
from indextts.infer_v2_5 import IndexTTS2

tts = IndexTTS2(
    cfg_path="checkpoints/config.yaml",
    model_dir="checkpoints",
    use_bf16=True,
    use_qwen_emo=True
)
```

Use BF16 on supported NVIDIA hardware.

Do not reload the model for every request.

Architecture:

```text
Application starts
      ↓
ModelManager initializes
      ↓
IndexTTS 2.5 loaded once
      ↓
GPU model stays resident
      ↓
Generation jobs reuse model
```

Provide model states:

```text
Not loaded
Loading
Ready
Generating
Error
```

Expose these through the frontend.

---

# 4. Voice Cloning

The main feature is zero-shot speaker cloning.

User can:

```text
Upload voice
Record microphone
Choose saved voice
```

Accept:

```text
WAV
MP3
FLAC
M4A
OGG
```

Convert internally to the format expected by IndexTTS.

Recommended reference length:

```text
5–15 seconds
```

UI should explain that clean speech produces the best clone.

Reference audio editor must allow:

```text
trim beginning
trim ending
remove unwanted section
normalize
denoise
play
pause
zoom waveform
```

The cloned voice should become a reusable:

```text
Voice Profile
```

Example:

```text
Voice Profile

Name:
Adeel Voice

Reference:
adeel_clean.wav

Duration:
11.4 sec

Created:
2026-09-13

Notes:
Neutral clean microphone sample
```

Store the original reference and optional cleaned reference separately.

Never overwrite the original recording.

---

# 5. Voice Library

Create a dedicated **Voices** page.

Cards should show:

```text
Voice name
Reference duration
Created date
Favorite
Preview
Rename
Duplicate
Delete
Edit
```

Allow tags:

```text
Male
Female
Narrator
Character
Urdu
English
Hindi
Custom
```

Tags are user-defined metadata, not automatically assumed attributes.

Allow searching voices.

---

# 6. Main TTS Studio

Main screen should contain approximately:

```text
┌──────────────────────────────────────────────┐
│ Voice Studio                                 │
├───────────┬──────────────────────────────────┤
│ Voice     │ Script Editor                    │
│ Emotion   │                                  │
│ Settings  │                                  │
│           │                                  │
│           ├──────────────────────────────────┤
│           │ Waveform / Generated Takes       │
└───────────┴──────────────────────────────────┘
```

Script editor should support long multiline scripts.

Show:

```text
characters
words
estimated duration
```

Buttons:

```text
Generate
Generate Variation
Generate 3 Takes
Stop
Clear
```

---

# 7. Emotion Control — Critical Feature

Implement ALL IndexTTS 2.5 emotion-control approaches.

The user should choose:

```text
Emotion Mode

● Emotion Mixer
○ Emotion Description
○ Auto Emotion From Text
○ Emotion Reference Audio
○ Speaker Original Emotion
```

These modes must map correctly to IndexTTS rather than being fake frontend controls.

---

# 8. Emotion Mixer

IndexTTS uses eight emotion dimensions.

Create sliders for:

```text
Happy
Angry
Sad
Afraid
Disgusted
Melancholic
Surprised
Calm
```

Example UI:

```text
Happy        ━━━━━━━━━━━ 0.80
Angry        ━━━         0.15
Sad          ━           0.05
Afraid       ━           0.00
Disgusted    ━           0.00
Melancholic  ━━━         0.20
Surprised    ━━━━━       0.35
Calm         ━━━━━━      0.45
```

Internally generate:

```python
emo_vector = [
    happy,
    angry,
    sad,
    afraid,
    disgusted,
    melancholic,
    surprised,
    calm
]
```

Do not reorder these values.

Show exact numerical values.

Allow double-click/reset.

Provide:

```text
Reset
Normalize
Randomize
Save Preset
```

---

# 9. Emotion Strength

Expose:

```text
Emotion Strength
```

mapped to:

```python
emo_alpha
```

Range:

```text
0.0 – 1.0
```

Show:

```text
0%
25%
50%
75%
100%
```

Default to a natural moderate value where appropriate.

Include tooltip explaining:

```text
Higher values increase the influence of the selected
emotion/reference. Extreme values may sound less natural.
```

---

# 10. Emotion Description

Allow natural-language emotional direction.

Example:

```text
Speak softly with sadness, like someone remembering
an old friend, but avoid crying.
```

Another:

```text
Excited and energetic, but still professional.
```

Another:

```text
Angry and frustrated while trying to remain controlled.
```

Use IndexTTS emotion-description support.

UI:

```text
Emotion Description

[ ________________________________________ ]
[ ________________________________________ ]

Strength: 60%

Generate
```

Save common descriptions as presets.

---

# 11. Automatic Emotion From Text

Implement:

```text
Auto Detect Emotion
```

Use IndexTTS 2.5 text-driven emotion functionality.

The model should be instantiated appropriately to support this functionality.

When enabled:

```text
Script
 ↓
Emotion analysis
 ↓
IndexTTS emotional speech
```

Expose emotion strength.

Allow user to override it.

---

# 12. Emotion Reference Audio

Allow separate:

```text
Speaker Reference Audio
```

and:

```text
Emotion Reference Audio
```

Example:

```text
Speaker:
my_voice.wav

Emotion:
sad_actor.wav
```

Result:

```text
identity from speaker reference
+
expression from emotion reference
```

User should be able to upload, preview, trim and normalize emotion reference audio.

Expose `emo_alpha`.

Clearly label speaker identity and emotional reference separately so users don't confuse them.

---

# 13. Emotion Presets

Ship UI presets such as:

```text
Neutral
Happy
Very Happy
Excited
Sad
Deep Sadness
Melancholic
Angry
Controlled Anger
Fearful
Surprised
Calm
Warm
Serious
Storytelling
Energetic
Soft
```

Presets should be editable.

Do not hard-code them so they cannot be changed.

Example:

```json
{
  "name": "Controlled Anger",
  "vector": {
    "happy": 0.0,
    "angry": 0.72,
    "sad": 0.08,
    "afraid": 0.0,
    "disgusted": 0.12,
    "melancholic": 0.05,
    "surprised": 0.0,
    "calm": 0.38
  },
  "alpha": 0.7
}
```

Allow unlimited custom presets.

---

# 14. Mixed Emotion Presets

Support combinations.

Examples:

```text
Happy + Surprised
Sad + Calm
Angry + Calm
Fear + Surprise
Melancholic + Calm
Happy + Calm
```

Users should be able to see exactly which emotion sliders are active.

---

# 15. Speaking Speed

Expose IndexTTS 2.5:

```python
duration_factor
```

UI:

```text
Speaking Speed

Faster ─────────●──────── Slower

0.5                1.0                2.0
```

Remember:

```text
duration_factor < 1
= shorter/faster

duration_factor > 1
= longer/slower
```

Display user-friendly speed descriptions instead of confusing users.

For example:

```text
0.75 → Faster
1.00 → Normal
1.20 → Slightly slower
1.50 → Slow
```

---

# 16. Languages

Create a language selector based on the actual languages supported by the installed IndexTTS 2.5 version.

Do not invent unsupported language support.

Example UI:

```text
Language

[ Auto / Supported Language ▼ ]
```

Pass the required `lang` value to IndexTTS.

Provide automatic script detection only as a convenience.

Allow manual override.

If the user enters unsupported text/language, display a clear warning rather than silently generating bad output.

---

# 17. Multiple Takes

Every generation should be a **Take**.

Example:

```text
Take 1
Take 2
Take 3
```

Each take stores:

```text
text
speaker
emotion mode
emotion vector
emotion alpha
emotion prompt
emotion reference
language
duration factor
seed if applicable
generation time
audio file
timestamp
```

User can compare takes using:

```text
A/B
```

and favorite the best one.

---

# 18. Generate Variations

Provide:

```text
Generate 1
Generate 2
Generate 3
Generate 5
```

variations.

Run sequentially by default to avoid unnecessary VRAM pressure.

Show progress:

```text
Generating 2 / 5
```

Do not start five simultaneous GPU inference processes.

---

# 19. Advanced Generation Settings

Create collapsible:

```text
Advanced
```

panel.

Expose only real model settings available through IndexTTS.

Potential controls:

```text
random emotion sampling
seed
emotion alpha
duration factor
language
```

Do not fabricate unsupported sampling parameters.

If a parameter is unavailable in the installed version, hide it.

---

# 20. Audio Waveform

Use WaveSurfer.js.

Show every generated clip visually.

Features:

```text
play
pause
seek
zoom
selection
loop selection
time ruler
current position
duration
```

Waveform should remain responsive with longer clips.

---

# 21. Audio Editor

Build a non-destructive audio editor.

Operations:

```text
Trim
Cut
Delete selection
Keep selection
Fade in
Fade out
Insert silence
Remove silence
Normalize
Amplify
```

Use an edit-operation stack rather than destructively modifying the original immediately.

Architecture:

```text
Original generated audio
        ↓
Edit operations
        ↓
Preview render
        ↓
Final export
```

Provide:

```text
Undo
Redo
Reset
```

---

# 22. Silence Removal

Implement:

```text
Remove Silence
```

Controls:

```text
Threshold
Minimum silence duration
Keep padding
```

Example:

```text
Silence threshold: -45 dB
Minimum duration: 300 ms
Keep padding: 100 ms
```

Never aggressively cut words.

Preview before applying.

---

# 23. Audio Enhancer

Create an:

```text
Enhance
```

panel.

Pipeline:

```text
Generated Audio
       ↓
Noise Reduction
       ↓
High-pass filter
       ↓
Optional EQ
       ↓
Compression
       ↓
De-esser
       ↓
Normalization
       ↓
Limiter
       ↓
Final audio
```

Every processor must be individually switchable.

---

# 24. AI Noise Reduction

Support optional speech enhancement.

Preferred option:

```text
DeepFilterNet
```

Provide:

```text
AI Denoise OFF/ON
```

and intensity where supported.

Do NOT force DeepFilterNet on every output.

IndexTTS output may already be clean.

Enhancement is optional.

For imported/reference recordings, make denoise more prominent.

---

# 25. Simple Noise Gate

Also provide a lightweight:

```text
Noise Gate
```

Controls:

```text
Threshold
Attack
Release
```

Useful for microphone reference recordings.

---

# 26. Equalizer

Provide simple parametric/preset EQ.

Basic controls:

```text
Low
Mid
High
```

Advanced mode:

```text
80 Hz
160 Hz
320 Hz
640 Hz
1.2 kHz
2.5 kHz
5 kHz
10 kHz
```

Presets:

```text
Flat
Warm
Bright
Narration
Podcast
Clear Speech
Deep Voice
```

Audio processing should remain high-quality.

---

# 27. Compressor

Controls:

```text
Threshold
Ratio
Attack
Release
Makeup gain
```

Provide easy mode:

```text
Off
Light
Medium
Strong
```

---

# 28. De-Esser

Provide optional de-essing.

Controls:

```text
frequency
threshold
amount
```

Useful for sharp artificial S sounds.

---

# 29. High-Pass Filter

Provide:

```text
Off
60 Hz
80 Hz
100 Hz
120 Hz
```

Useful for removing low-frequency rumble.

---

# 30. Loudness Normalization

Support:

```text
Peak normalization
LUFS normalization
```

Presets:

```text
Podcast
YouTube
Audiobook
Custom
```

Allow custom target.

Never clip audio.

---

# 31. Limiter

Add final true/peak limiter where practical.

Expose:

```text
Ceiling
```

Example:

```text
-1 dB
```

---

# 32. Enhancement Presets

Include:

```text
Natural
Clean Voice
Podcast
Narrator
YouTube
Warm Voice
Bright Voice
Broadcast
No Processing
```

These presets control the processing chain only.

Keep TTS/emotion presets separate from audio-processing presets.

---

# 33. Before/After Comparison

Enhancer should provide:

```text
Original
Processed
```

A/B toggle.

User should instantly compare both without re-generating TTS.

---

# 34. Reference Audio Cleaner

When uploading a cloning reference, show:

```text
Clean Reference
```

Pipeline:

```text
remove DC offset
convert mono
resample correctly
remove long silence
optional noise reduction
normalize safely
```

Allow:

```text
Original
Cleaned
```

comparison.

Never force aggressive cleanup.

Voice identity can be damaged by excessive processing.

---

# 35. Microphone Recording

Add:

```text
Record Voice
```

through browser microphone access.

Show:

```text
input level
timer
waveform
record
stop
play
retry
save as voice
```

Warn if:

```text
audio too quiet
audio clipping
reference too short
reference contains excessive silence
```

---

# 36. Reference Quality Analyzer

Analyze uploaded/recorded samples.

Display something like:

```text
Reference Quality

Duration: 10.6s      Good
Peak: -3.2 dB        Good
Noise level: Low     Good
Clipping: None       Good
Silence: 8%          Good

Overall:
Excellent
```

Do not pretend to calculate metrics that are not actually measured.

---

# 37. Text Editor

The script editor should support:

```text
Find
Replace
Undo
Redo
Character count
Word count
Paragraph count
```

Add formatting helpers that affect generation metadata, not rich-text HTML.

---

# 38. Script Segments

Allow splitting a long script into segments:

```text
Segment 1
Segment 2
Segment 3
```

Each segment may have its own:

```text
emotion
speed
voice
language
```

Example:

```text
Segment 1
Calm

"I knew something was wrong."

Segment 2
Fear

"Then I heard footsteps behind me."

Segment 3
Angry

"Who are you? Get away from me!"
```

Generate them separately and concatenate smoothly.

---

# 39. Timeline Mode

Add an optional advanced timeline:

```text
[ Segment 1 ][ Segment 2 ][ Segment 3 ]
```

Each segment displays:

```text
speaker
emotion
duration
waveform
```

Allow drag-to-reorder.

---

# 40. Multi-Character Dialogue

Support multiple saved speakers.

Example:

```text
Narrator:
It was almost midnight.

Adeel:
Did you hear that?

Character 2:
Hear what?
```

Assign a different Voice Profile to every character.

Each line/segment can have separate emotion settings.

Generate a combined final track.

---

# 41. Generation Queue

Create a safe GPU queue.

Architecture:

```text
Request
   ↓
Job Queue
   ↓
GPU Worker
   ↓
IndexTTS
   ↓
Audio Processing
   ↓
Complete
```

Jobs:

```text
Queued
Generating
Processing
Completed
Failed
Cancelled
```

Use WebSockets to push progress to frontend.

---

# 42. Cancel Generation

User should be able to press:

```text
Cancel
```

Do not freeze the UI.

Clean temporary files after cancellation.

GPU memory should recover.

---

# 43. GPU Monitoring

Show status in application:

```text
GPU
NVIDIA RTX 5060 Ti

VRAM
8.2 / 16 GB

Model
IndexTTS 2.5

Precision
BF16

Status
Ready
```

Use NVML when available.

Do not poll excessively.

---

# 44. RTX 5060 Ti Optimization

Optimize specifically for a 16 GB NVIDIA GPU.

Preferred:

```text
BF16 when supported
single persistent model
torch.inference_mode()
no duplicate model copies
sequential generation queue
automatic cleanup of intermediate tensors
```

Do NOT call:

```python
torch.cuda.empty_cache()
```

after every tiny operation unless it is actually necessary.

Avoid unnecessary CPU↔GPU transfers.

Provide optional:

```text
Low Memory Mode
```

for systems where VRAM is constrained.

---

# 45. Model Loader

Create settings:

```text
Load model at startup
Unload model
Reload model
```

Display estimated/actual memory after model initialization.

Handle model-loading failures gracefully.

---

# 46. History

Every generation appears in:

```text
History
```

Show:

```text
timestamp
voice
script preview
emotion
duration
generation time
favorite
```

Allow:

```text
play
edit
regenerate
duplicate settings
download
delete
```

---

# 47. Projects

Support saved projects.

Example:

```text
Projects

YouTube Narration
Audiobook Chapter 01
Game Character
Urdu Story
Voice Tests
```

A project stores:

```text
script
segments
voices
takes
audio edits
TTS settings
enhancement settings
exports
```

Auto-save locally.

---

# 48. Autosave

Autosave project state.

Never lose the script because the browser refreshes.

Show:

```text
Saved
```

and:

```text
Unsaved changes
```

---

# 49. Export

Support:

```text
WAV
FLAC
MP3
```

WAV should be the preferred lossless master.

Export options:

```text
sample rate
bit depth where appropriate
mono/stereo
MP3 bitrate
filename
metadata
```

Preserve a high-quality original master.

---

# 50. Batch Export

Allow selecting multiple takes:

```text
☑ Take 1
☑ Take 3
☑ Take 7

Export Selected
```

Optionally create ZIP.

---

# 51. Audio Metadata

Optionally write:

```text
project
speaker
date
take
```

to supported formats.

Do not include cloning reference paths in externally exported metadata.

---

# 52. Preset System

There should be three independent preset types:

```text
Voice/TTS Preset
Emotion Preset
Enhancement Preset
```

For example:

```text
Preset:
Calm YouTube Narrator

Voice:
Adeel

Emotion:
Calm 0.65
Melancholic 0.08

Speed:
1.05 duration factor

Enhancement:
Podcast Light
```

Allow import/export JSON presets.

---

# 53. Settings

Settings page:

```text
General
Models
GPU
Audio
Storage
Interface
Advanced
```

General:

```text
default project folder
autosave
theme
```

Models:

```text
IndexTTS checkpoint path
model status
reload model
```

GPU:

```text
device
precision
low-memory mode
```

Audio:

```text
default export
sample rate
format
```

Storage:

```text
cache
temporary files
generation directory
clear cache
```

---

# 54. Dark UI

Default to a polished dark theme.

Design inspiration:

```text
professional audio workstation
modern AI application
minimal clutter
high information density
```

Avoid:

```text
giant gradient cards everywhere
oversized rounded boxes
toy-looking UI
```

Use restrained visual hierarchy.

---

# 55. Studio Layout

Suggested desktop layout:

```text
┌─────────────────────────────────────────────────────────┐
│ AI Voice Studio                          GPU Ready ●     │
├────────┬───────────────────────────┬────────────────────┤
│ Voices │ Script                    │ Voice Settings     │
│        │                           │                    │
│        │                           │ Emotion            │
│        │                           │ Speed              │
│        │                           │ Language           │
│        │                           │                    │
│        │                           │ [ Generate ]       │
├────────┴───────────────────────────┴────────────────────┤
│                   Waveform                             │
├─────────────────────────────────────────────────────────┤
│ Takes │ Editor │ Enhance │ History                     │
└─────────────────────────────────────────────────────────┘
```

Make it responsive, but desktop is the primary target.

---

# 56. Keyboard Shortcuts

Examples:

```text
Ctrl + Enter
Generate

Space
Play/Pause

Ctrl + S
Save project

Ctrl + Z
Undo

Ctrl + Shift + Z
Redo

Delete
Delete selected waveform region
```

Do not override browser shortcuts irresponsibly.

---

# 57. API Design

Example backend endpoints:

```text
POST /api/generate
POST /api/generate/batch
POST /api/generate/cancel

GET  /api/jobs/{id}
GET  /api/jobs

POST /api/voices
GET  /api/voices
GET  /api/voices/{id}
DELETE /api/voices/{id}

POST /api/audio/enhance
POST /api/audio/trim
POST /api/audio/normalize
POST /api/audio/denoise

GET  /api/projects
POST /api/projects
PUT  /api/projects/{id}
DELETE /api/projects/{id}

GET  /api/history
GET  /api/system/gpu
GET  /api/system/model

WS   /ws/jobs
```

Validate all input.

---

# 58. Generation Request

Create a strongly typed request approximately:

```python
class GenerateRequest(BaseModel):
    text: str

    voice_id: str

    language: str | None = None

    emotion_mode: Literal[
        "speaker",
        "vector",
        "description",
        "auto_text",
        "reference"
    ]

    emotion_vector: list[float] | None = None

    emotion_alpha: float = 0.6

    emotion_text: str | None = None

    emotion_reference_id: str | None = None

    duration_factor: float = 1.0

    use_random: bool = False
```

Validate:

```text
emotion_alpha 0–1
emotion vector exactly 8 values
duration factor supported model range
non-empty text
existing voice
supported language
```

---

# 59. IndexTTS Adapter

Do NOT scatter IndexTTS calls throughout the code.

Create:

```text
IndexTTSEngine
```

with a clean interface.

Example:

```python
class IndexTTSEngine:

    async def generate(
        self,
        text,
        speaker_audio,
        output_path,
        language=None,
        emotion_vector=None,
        emotion_text=None,
        emotion_audio=None,
        emotion_alpha=0.6,
        use_text_emotion=False,
        use_random=False,
        duration_factor=1.0,
    ):
        ...
```

This allows replacing/upgrading the model later.

---

# 60. Future Model Support

Architecture should eventually allow:

```text
IndexTTS 2.5
Qwen3-TTS
Chatterbox
Fish Speech
```

BUT:

Do not implement these extra models in Version 1.

Build a clean provider interface so they can be added later.

IndexTTS 2.5 remains the only required TTS backend.

---

# 61. Text Sanitization

Handle:

```text
Unicode
smart quotes
multiple whitespace
line breaks
very long paragraphs
```

Do not destroy punctuation because punctuation contributes to prosody.

Keep original text stored in project.

---

# 62. Long Text

Do not send unlimited text blindly.

Implement intelligent text splitting.

Prefer boundaries:

```text
paragraph
sentence
punctuation
```

Never cut a word.

Generate chunks.

Then combine audio with configurable silence:

```text
sentence gap
paragraph gap
```

Preserve consistent speaker and emotion.

---

# 63. Long-Form Voice Consistency

For long generations:

```text
same speaker reference
same parameters
same selected language
```

should be maintained across chunks.

Allow:

```text
Regenerate only this segment
```

instead of regenerating entire narration.

---

# 64. Audio Cache

Cache completed generation inputs using a deterministic hash where appropriate.

Hash may include:

```text
script
voice reference hash
emotion settings
language
duration factor
model version
```

Do not regenerate identical outputs unnecessarily when deterministic generation is requested.

Provide:

```text
Disable Cache
```

in advanced settings.

---

# 65. File Safety

Never trust uploaded filenames.

Generate internal UUIDs.

Validate:

```text
MIME
extension
size
duration
```

Do not allow path traversal.

Temporary uploads should be deleted automatically.

---

# 66. Local Privacy

This project is intentionally local.

Display:

```text
Local Processing
Your voice recordings and generated speech remain on this computer.
```

Do not secretly upload:

```text
voice recordings
scripts
generations
analytics
```

to any remote service.

---

# 67. Consent / Responsible Voice Cloning

Add a simple notice when importing a new voice:

```text
Only clone voices you own or have permission to use.
```

Do not introduce intrusive friction for ordinary personal usage, but make consent expectations clear.

---

# 68. Logging

Implement structured logs.

Example:

```text
Model loaded
GPU detected
Voice loaded
Generation started
Generation finished
Audio enhanced
Export finished
```

Never log:

```text
full private scripts by default
raw audio contents
sensitive filesystem information unnecessarily
```

Provide:

```text
logs/app.log
```

with rotation.

---

# 69. Diagnostics

Create:

```text
System Diagnostics
```

Check:

```text
Python version
PyTorch
CUDA
GPU
VRAM
FFmpeg
IndexTTS checkpoints
DeepFilterNet if enabled
write permissions
```

UI should show:

```text
✓ CUDA available
✓ RTX 5060 Ti
✓ IndexTTS loaded
✓ FFmpeg available
✓ Audio processor available
```

---

# 70. Windows Installer Script

Provide:

```text
scripts/install.ps1
```

It should:

```text
create Python environment
install PyTorch appropriately
install requirements
check CUDA
download/setup model instructions
install frontend dependencies
verify FFmpeg
run diagnostics
```

Do not silently install unrelated system software.

---

# 71. Start Script

Provide:

```text
start.ps1
```

Start:

```text
FastAPI backend
React frontend
```

Then open:

```text
http://localhost:5173
```

in the browser.

Later production mode may have FastAPI serve the compiled frontend from:

```text
http://127.0.0.1:8000
```

Prefer a single local URL for packaged production.

---

# 72. Production Build

Create:

```text
npm run build
```

and allow FastAPI to serve:

```text
frontend/dist
```

Final application:

```text
start.bat / start.ps1
       ↓
Backend starts
       ↓
IndexTTS initializes
       ↓
Browser automatically opens
       ↓
Voice Studio ready
```

---

# 73. Error Handling

Frontend errors must be human-readable.

Examples:

```text
IndexTTS model is not loaded.

Reference recording is too short.

CUDA ran out of memory.

FFmpeg was not found.

Emotion-reference audio could not be decoded.
```

Never just show:

```text
500 Internal Server Error
```

Provide technical details under:

```text
Show Details
```

---

# 74. CUDA Out-of-Memory Recovery

If CUDA OOM occurs:

```text
cancel current generation
release intermediate objects
attempt safe CUDA cache cleanup
keep backend alive
display helpful warning
```

Do not crash the whole application.

Suggest:

```text
shorter segment
sequential takes
Low Memory Mode
close other GPU applications
```

---

# 75. Generation Performance Information

Record per generation:

```text
generation time
audio duration
real-time factor
peak VRAM if available
```

Example:

```text
Audio:
14.2 sec

Generated:
7.8 sec

RTF:
0.55x
```

Display under optional diagnostics.

---

# 76. Comparison Mode

Allow selecting two takes.

UI:

```text
A                           B
Take 4                      Take 7

Happy 0.55                  Happy 0.35
Calm 0.40                   Calm 0.65
Emotion Alpha 0.7           Emotion Alpha 0.6

[Play A]                    [Play B]
```

Useful for tuning emotions.

---

# 77. Favorite Take

Every take gets:

```text
♡ / ♥
```

Project can have:

```text
Primary Take
```

---

# 78. Clone Test

After creating a Voice Profile, allow:

```text
Test Voice
```

with a short predefined or user-entered sentence.

Do not require creating a whole project just to test a speaker.

---

# 79. Emotion Lab

Create a dedicated:

```text
Emotion Lab
```

page.

User enters one sentence and generates it with several emotional variations.

For example:

```text
Text:

"I didn't expect to see you here."
```

Generate:

```text
Neutral
Happy
Sad
Angry
Afraid
Surprised
Calm
Melancholic
```

Display as cards for instant comparison.

This is one of the key features.

---

# 80. Emotion Matrix

Optional advanced visualization:

```text
Emotion       Intensity
Happy         0.00
Angry         0.00
Sad           0.75
Afraid        0.10
Disgusted     0.00
Melancholic   0.45
Surprised     0.00
Calm          0.20
```

Allow saving this exact matrix as a preset.

---

# 81. Voice + Emotion Separation

The interface should constantly reinforce the distinction:

```text
VOICE
Who is speaking?

EMOTION
How are they speaking?
```

Never merge those concepts into a single selector.

This separation is one of the reasons IndexTTS 2.5 is being selected.

---

# 82. Audio Processing Order

Use a deterministic audio-processing chain.

Recommended default:

```text
Input
 ↓
Denoise (optional)
 ↓
High-pass
 ↓
EQ
 ↓
De-esser
 ↓
Compression
 ↓
Gain
 ↓
LUFS normalization
 ↓
Limiter
 ↓
Output
```

Users may disable processors.

Avoid cumulative clipping.

---

# 83. Non-Destructive Processing

Always preserve:

```text
raw generation
```

separately from:

```text
processed version
```

The user should be able to return to raw audio at any point.

---

# 84. Performance

The application should remain responsive while generating.

Never run heavy inference on FastAPI's primary event loop.

Use worker/thread/process architecture appropriate for GPU inference.

Do not accidentally load a second IndexTTS instance in a worker process.

---

# 85. Database

Use:

```text
SQLite
```

for local metadata.

Store large audio files on disk.

Database stores paths and metadata rather than audio BLOBs.

Tables approximately:

```text
voices
projects
segments
generations
takes
presets
exports
settings
```

---

# 86. Backup

Provide:

```text
Export Project
```

into something like:

```text
my-project.voiceproject.zip
```

containing:

```text
project.json
required voice references
audio
settings
```

Allow later import.

---

# 87. First-Run Experience

On first startup:

```text
Welcome to Local Voice Studio

1. Check GPU
2. Check IndexTTS model
3. Configure storage
4. Add first voice
```

Do not require an online account.

No login system is required.

---

# 88. Dashboard

Dashboard should show:

```text
New Generation
New Voice
New Project

Recent Projects
Recent Voices
Recent Generations

GPU Status
Model Status
```

---

# 89. UI Quality

Pay particular attention to:

```text
spacing
typography
loading states
hover states
disabled states
tooltips
keyboard accessibility
waveform responsiveness
smooth tabs
clear progress indicators
```

Avoid creating a developer-looking demo.

It should look like a real finished product.

---

# 90. Do Not Fake Functionality

Critical rule:

If IndexTTS does not expose a specific model parameter:

```text
DO NOT pretend it exists.
```

Audio post-processing features may be implemented separately, but model-level controls must accurately correspond to actual IndexTTS functionality.

Document the distinction between:

```text
IndexTTS generation settings
```

and:

```text
post-processing settings
```

---

# 91. Dependency Isolation

Pin major dependencies.

Do not blindly install newest versions if incompatible with IndexTTS.

Test:

```text
PyTorch
transformers
tokenizers
numpy
scipy
FastAPI
```

against IndexTTS requirements.

Provide documented known-good versions.

---

# 92. Testing

Write tests for:

```text
emotion-vector validation
project save/load
voice profile creation
file validation
audio trimming
normalization
preset loading
generation request serialization
long-text splitting
```

Add GPU integration tests separately so ordinary unit tests don't require IndexTTS.

---

# 93. README

README must cover:

```text
Requirements
Installation
Model download
Starting app
Adding voice
Generating speech
Emotion controls
Enhancement
Audio editing
Exporting
Troubleshooting
RTX 5060 Ti recommendations
```

Include screenshots later through placeholders.

---

# 94. Development Phases

Implement in this order.

## Phase 1

```text
FastAPI
React
IndexTTS 2.5 load
voice upload
basic TTS
WAV playback
```

Do not continue until basic generation works.

## Phase 2

```text
Voice profiles
Emotion vectors
Emotion alpha
Emotion descriptions
Auto emotion
Emotion reference audio
Speed
Language
```

## Phase 3

```text
Waveform
Takes
History
Projects
Presets
```

## Phase 4

```text
Trim
Cut
Fade
Silence editing
Undo/redo
```

## Phase 5

```text
Denoise
EQ
compressor
de-esser
normalization
limiter
enhancement presets
```

## Phase 6

```text
Script segmentation
Timeline
Multi-character generation
Batch generation
```

## Phase 7

```text
optimization
diagnostics
installer
tests
production packaging
```

Do not attempt to implement the entire application as one enormous file.

---

# 95. Minimum Usable Version

The first milestone is complete when I can:

```text
1. Start application

2. Open browser

3. Upload a 5–15 second voice sample

4. Save it as a Voice Profile

5. Type text

6. Select language

7. Select emotion

8. Mix:
   Happy
   Angry
   Sad
   Afraid
   Disgusted
   Melancholic
   Surprised
   Calm

9. Adjust emotion strength

10. Adjust speaking speed

11. Generate speech

12. View waveform

13. Play output

14. Enhance output

15. Trim output

16. Export WAV
```

After this works reliably, implement advanced features.

---

# 96. Final Product Goal

The finished application should behave like:

```text
                 LOCAL AI VOICE STUDIO
                          │
             ┌────────────┴────────────┐
             │                         │
        VOICE CLONING              SCRIPT
             │                         │
       Voice Profiles           Text / Segments
             │                         │
             └────────────┬────────────┘
                          │
                    INDEXTTS 2.5
                          │
         ┌────────────────┼────────────────┐
         │                │                │
     Emotion           Speed           Language
         │
 ┌───────┼────────┬────────────┐
 │       │        │            │
Vector  Text    Auto       Reference
Mixer   Prompt  Emotion     Audio
 │
 ▼
Generated Voice
 │
 ▼
Multiple Takes
 │
 ▼
Waveform Editor
 │
 ▼
Audio Enhancement
 │
 ├── Denoise
 ├── EQ
 ├── De-esser
 ├── Compressor
 ├── Normalize
 └── Limiter
 │
 ▼
Final Master
 │
 ▼
WAV / FLAC / MP3
```

The application should make it possible to take **one clean recording of a speaker** and turn it into a reusable local voice capable of producing many different emotional performances while preserving speaker identity as well as IndexTTS 2.5 allows.

Priorities, in order:

```text
1. Voice-cloning quality
2. Speaker consistency
3. Emotion control
4. Natural speech
5. Stable RTX 5060 Ti 16 GB operation
6. Audio quality
7. Easy editing
8. Good UI
9. Fast workflow
10. Advanced features
```

Do not sacrifice voice quality simply to make generation faster.

Build the application incrementally, keep modules clean, and verify each phase before layering additional features on top.
