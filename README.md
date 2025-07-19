# 🔊 FastRTC STT & TTS Integration README

This README outlines the modifications made to the **FastRTC** library to support:

- ✅ Text input/output in STT (Speech-to-Text) and TTS (Text-to-Speech)
- 🔁 Streaming TTS responses via WebSocket
- 🛠 Updates to core FastRTC files inside your `.venv`

---

## 📌 Summary of Updates

| Feature                | Description                                                                          |
|------------------------|--------------------------------------------------------------------------------------|
| 🔁 **Streaming TTS**    | TTS now streams audio in chunks over WebSocket using text input                     |
| 💬 **Text I/O Support** | STT and TTS now both support plain text input/output for seamless integration       |
| 🔄 **WebSocket Update** | WebSocket support improved for real-time STT transcription and TTS audio delivery   |
| 🧠 **Track Handling**   | Enhanced STT track processing to extract, buffer, and return text from audio input  |

---

## 📂 FastRTC Files to Replace

To activate the new features, **replace the following files** inside your Python virtual environment's FastRTC library.

---

### 🔊 Replace TTS WebSocket File

#### ✅ File: `tts/websockets.py`

**Instructions:**

1. Locate this path:
    ```
    .venv/lib/python<version>/site-packages/fastrtc/websockets.py
    ```

    Replace `<version>` with your Python version, e.g., `python3.10`.

2. Replace the `websockets.py` file with your updated version that includes:
    - Text input handling for TTS
    - Streaming audio response via WebSocket

---

### 🎤 Replace STT Files

#### ✅ File: `stt/tracks.py`

**Instructions:**

1. Go to:
    ```
    .venv/lib/python<version>/site-packages/fastrtc/tracks.py
    ```

---

#### ✅ File: `stt/websockets.py`

**Instructions:**

1. Go to:
    ```
    .venv/lib/python<version>/site-packages/fastrtc/websockets.py
    ```

2. Replace the file with the updated version that:
    - Handles audio input over WebSocket
    - Sends real-time transcription responses

---

## 🔄 After Replacing Files

1. **Restart your app/server** to apply changes.

2. Ensure your environment is pointing to the `.venv` you're modifying.

---


