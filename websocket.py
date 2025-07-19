import asyncio
import base64
import logging
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect, WebSocketState
import numpy as np
 
from .utils import (
    split_output,  # Your util to parse (frame, additional) tuple
    audio_to_float32, audio_to_int16
)
 
logger = logging.getLogger(__file__)
 
def convert_to_mulaw(audio_data: np.ndarray, original_rate: int, target_rate: int) -> bytes:
    import librosa, audioop
    audio_data = audio_to_float32(audio_data)
    if original_rate != target_rate:
        audio_data = librosa.resample(audio_data, orig_sr=original_rate, target_sr=target_rate)
    audio_data = audio_to_int16(audio_data)
    return audioop.lin2ulaw(audio_data, 2)
 
class WebSocketHandler:
    def __init__(
        self,
        stream_handler,
        set_handler,
        clean_up,
        additional_outputs_factory,
    ):
        self.stream_handler = stream_handler
        self.websocket: WebSocket | None = None
        self.stream_id: str | None = None
        self.quit = asyncio.Event()
        self.clean_up = clean_up
        self.set_handler = set_handler
        self.set_additional_outputs_factory = additional_outputs_factory
        self.set_additional_outputs = None
        self.playing_durations = []
        self._streaming_task = None
 
    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket
        loop = asyncio.get_running_loop()
        self.stream_handler._loop = loop
 
        was_disconnected = False
        try:
            while not self.quit.is_set():
                if websocket.application_state != WebSocketState.CONNECTED:
                    was_disconnected = True
                    break
 
                message = await websocket.receive_json()
 
                if message["event"] == "start":
                    self.stream_id = message.get("websocket_id") or message.get("streamSid")
                    self.set_additional_outputs = self.set_additional_outputs_factory(self.stream_id)
                    await self.set_handler(self.stream_id, self)
                elif message["event"] == "text":
                    audio_payload = message["media"]["payload"]
                    # Set up handler for this text
                    if hasattr(self.stream_handler, "receive"):
                        await self.stream_handler.receive(audio_payload)
                    # Start streaming for this text if not already running
                    if self._streaming_task is None or self._streaming_task.done():
                        self._streaming_task = asyncio.create_task(self._emit_streaming_loop())
                elif message["event"] == "stop":
                    self.quit.set()
                    return
                elif message["event"] == "ping":
                    await websocket.send_json({"event": "pong"})
        except WebSocketDisconnect:
            was_disconnected = True
        finally:
            if self._streaming_task:
                self._streaming_task.cancel()
            if not was_disconnected:
                await websocket.close()
            self.clean_up(self.stream_id)
 
    async def _emit_streaming_loop(self):
        try:
            # Main streaming logic: async iterate over handler.emit()
            async for output in self.stream_handler.emit():
                frame, additional = split_output(output)
 
                # Optionally handle addl outputs
                if additional:
                    if hasattr(self, "set_additional_outputs"):
                        self.set_additional_outputs(additional)
                    if isinstance(additional, CloseStream):
                        break
                if not isinstance(frame, tuple):
                    continue
 
                target_rate = (
                    8000 if getattr(self.stream_handler, "phone_mode", False)
                    else getattr(self.stream_handler, "output_sample_rate", 24000)
                )
                duration = np.atleast_2d(frame[1]).shape[1] / frame[0]
                mulaw_audio = convert_to_mulaw(frame[1], frame[0], target_rate=target_rate)
                audio_payload = base64.b64encode(mulaw_audio).decode("utf-8")
 
                if self.websocket and self.stream_id:
                    self.playing_durations.append(duration)
                    payload = {
                        "event": "media",
                        "media": {"payload": audio_payload},
                    }
                    logger.info("sent to the server")
                    await self.websocket.send_json(payload)
 
                await asyncio.sleep(0.02)  # tune for real-time pacing if needed
 
                            # After streaming ends, send stream_complete event:
            if self.websocket and self.stream_id:
                stream_done_msg = {
                    "event": "stream_finished",
                    "message": "Streaming complete"
                }
                await self.websocket.send_json(stream_done_msg)
                logger.info("Sent stream finished event to client")
 
        except asyncio.CancelledError:
            logger.debug("Streaming loop cancelled")
        except Exception as e:
            logger.exception("Error in streaming loop: %s", e)
 
