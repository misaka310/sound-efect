---
name: local-sfx-generation
description: Use when generating short non-musical sound effects or ambience.
---

# Local Sound Effect Generation

Generate a real local WAV with `C:\00_dev\68_sound-effect\tools\generate_audio.py` in `sfx` mode.

## Route the request

- Use this skill for sound effects such as clicks, impacts, doors, alerts, transitions, environmental ambience, and short game sounds.
- Do not use it for BGM, background music, songs, instrumental tracks, or game music. Route those to `local-bgm-generation`.
- Extract the intended source, material, action, environment, intensity, distance, and duration. Convert the request into a specific English prompt.
- When duration is omitted, use 5 seconds unless the effect clearly needs a shorter or longer tail.

## Generate

1. Confirm `C:\00_dev\68_sound-effect\tools\generate_audio.py` and `C:\00_dev\68_sound-effect\start.bat` exist.
2. If the local service is not running, start it with the documented launcher when the current execution environment permits local process startup. Do not make the user start it manually unless startup is blocked or requires an interactive step.
3. Run one request at a time:

```powershell
python C:\00_dev\68_sound-effect\tools\generate_audio.py --mode sfx --prompt "heavy iron door closing in a stone hallway, short low-frequency impact, no music" --duration 5 --json
```

4. Verify the newly returned WAV opens, has non-zero duration and signal, and is the file created by this request rather than an older cached output.

## Report

Report the absolute WAV path, model, duration, final English prompt, and verification result. If model access is denied, explain that the corresponding Hugging Face model license must be accepted and authentication completed; never store a token in the project.
