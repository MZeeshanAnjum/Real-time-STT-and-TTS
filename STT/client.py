<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Real-Time Transcription</title>
</head>
<body>
  <button id="start">Start Streaming</button>
  <h2>Transcription:</h2>
  <pre id="transcript"></pre>

  <script>
    const sampleRate = 48000;  // Must match server-side Whisper input rate
    const ws = new WebSocket("ws://localhost:8000/rtc/transcribe/websocket/offer");

    let audioCtx;
    let processor;

    ws.onopen = () => {
      console.log("WebSocket connected");
      ws.send(JSON.stringify({ event: "start", websocket_id: "test-stream" }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.event === "media" && msg.media) {
        if (msg.media.text) {
          document.getElementById("transcript").textContent += msg.media.text + " ";
        }
      }
    };

    document.getElementById("start").onclick = async () => {
      audioCtx = new AudioContext({ sampleRate });
      await audioCtx.resume();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const source = audioCtx.createMediaStreamSource(stream);

      processor = audioCtx.createScriptProcessor(4096, 1, 1);
      source.connect(processor);
      processor.connect(audioCtx.destination);

      processor.onaudioprocess = (event) => {
        const float32 = event.inputBuffer.getChannelData(0);
        const int16 = new Int16Array(float32.length);

        for (let i = 0; i < float32.length; i++) {
          let s = Math.max(-1, Math.min(1, float32[i]));
          int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Mu-law encode
        const muLaw = encodeMuLaw(int16);
        const b64 = btoa(String.fromCharCode(...muLaw));

        ws.send(JSON.stringify({
          event: "media",
          media: { payload: b64 }
        }));
      };
    };

    // Mu-law encoding functions
    function linearToMuLaw(sample) {
      const MU = 255;
      const MAX = 32635;

      let sign = (sample >> 8) & 0x80;
      if (sign !== 0) sample = -sample;
      if (sample > MAX) sample = MAX;

      let exponent = 7;
      for (let expMask = 0x4000; (sample & expMask) === 0 && exponent > 0; expMask >>= 1) {
        exponent--;
      }

      let mantissa = (sample >> ((exponent === 0) ? 4 : (exponent + 3))) & 0x0F;
      let muLawByte = ~(sign | (exponent << 4) | mantissa);
      return muLawByte & 0xFF;
    }

    function encodeMuLaw(int16Samples) {
      const output = new Uint8Array(int16Samples.length);
      for (let i = 0; i < int16Samples.length; i++) {
        output[i] = linearToMuLaw(int16Samples[i]);
      }
      return output;
    }
  </script>
</body>
</html>
