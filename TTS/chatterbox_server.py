import datetime
import logging
import numpy as np
import torch
from fastapi import FastAPI
from fastrtc import Stream, AsyncStreamHandler, wait_for_item
from chatterbox.tts import ChatterboxTTS
import asyncio
# Logging
logging.basicConfig(level=logging.INFO)
 
# Load model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=DEVICE)
model.prepare_conditionals(wav_fpath="neutral.mp3", exaggeration=0.5)
logging.info(model.sr)
 
# Warmup
for _ in model.generate_stream("warming up...", chunk_size=8):
    pass
 
 
class ChatterboxTTSHandler(AsyncStreamHandler):
    def __init__(self, model: ChatterboxTTS):
        super().__init__(output_sample_rate=model.sr)
        self.model = model
        self.audio_queue = asyncio.Queue()
        self.text = None
        self._stream_started = False
 
    def copy(self):
        return ChatterboxTTSHandler(self.model)
 
    async def start_up(self):
        logging.info("[TTS] Handler startup complete.")
 
    async def receive(self, text: str):
        self.text = text
        self._stream_started = False
        logging.info(f"[TTS] Received text chunk {text}")
 
    async def emit(self):
 
        if not self._stream_started and self.text is not None:
            self._stream_started = True
            for chunk, _ in self.model.generate_stream(
                text=self.text,
                chunk_size=25,
                exaggeration=0.5,
                temperature=0.8,
                cfg_weight=0.5,
                print_metrics=False,
            ):
                audio = chunk.squeeze(0).cpu().numpy().astype(np.float32)
                yield ((self.model.sr),audio)
           
 
 
 
    async def shutdown(self):
        logging.info("[TTS] Shutdown called.")
        self._stream_started = False
 
handler = ChatterboxTTSHandler(model)
 
# FastAPI app
app = FastAPI()
 
# FastRTC stream
stream = Stream(
    handler=handler,
    modality="audio",
    mode="send-receive",
)
stream.mount(app, path="/rtc/tts")
 
# sample_rate: 24000
