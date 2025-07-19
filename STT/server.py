# server.py
import io
import numpy as np
import soundfile as sf
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from faster_whisper import WhisperModel
from fastrtc import Stream, ReplyOnPause
from fastrtc.utils import AdditionalOutputs

from faster_whisper import WhisperModel

# Use int8 instead of int8_float16
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

import inspect
print(inspect.signature(AdditionalOutputs))

# Transcription function
def transcribe(audio: tuple[int, np.ndarray]):
    sr, samples = audio
    samples = np.asarray(samples)
    print(f"[INFO] Received {samples.shape} samples at {sr}Hz dtype {samples.dtype}")

    # If samples shape is (1, N), transpose to (N, 1)
    if samples.ndim == 2 and samples.shape[0] == 1:
        print(1)
        samples = samples.T

    # Ensure dtype is float32 or int16
    if samples.dtype != np.float32 and samples.dtype != np.int16:
        print(2)
        samples = samples.astype(np.float32)


    import io, soundfile as sf
    with io.BytesIO() as wav_io:
        sf.write(wav_io, samples, samplerate=sr, format="WAV")
        wav_io.seek(0)
        segments, _ = model.transcribe(wav_io, beam_size=5)
        full_transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        print("[TRANSCRIPT]",full_transcript )
            yield ((sr, samples.reshape(1, -1)), AdditionalOutputs(full_transcript))


# Setup FastAPI stream
app = FastAPI()

stream = Stream(
    handler=ReplyOnPause(transcribe),
    modality="audio",
    mode="send-receive"
)
stream.mount(app, path="/rtc/transcribe")
stream.ui.launch()
