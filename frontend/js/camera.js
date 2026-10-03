const Camera = (() => {
  let stream1 = null, recorder1 = null, chunks1 = [];
  let stream2 = null, recorder2 = null, chunks2 = [];

  function pickMime() {
    const opts = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm", "video/mp4"];
    for (const o of opts) if (window.MediaRecorder && MediaRecorder.isTypeSupported(o)) return o;
    return "";
  }

  async function requestCamera(withMic) {
    return navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: !!withMic,
    });
  }

  async function startVideo1() {
    stream1 = await requestCamera(false);
    recorder1 = new MediaRecorder(stream1, { mimeType: pickMime() });
    chunks1 = [];
    recorder1.ondataavailable = (e) => { if (e.data.size) chunks1.push(e.data); };
    recorder1.start(1000);
    Transitions.recIndicator(true);
    return true;
  }

  function stopVideo1() {
    return new Promise((resolve) => {
      if (!recorder1) return resolve(null);
      recorder1.onstop = () => {
        const blob = new Blob(chunks1, { type: pickMime() });
        stream1.getTracks().forEach(t => t.stop());
        recorder1 = null; stream1 = null;
        Transitions.recIndicator(false);
        resolve(blob);
      };
      recorder1.stop();
    });
  }

  async function startVideo2() {
    stream2 = await requestCamera(true);
    recorder2 = new MediaRecorder(stream2, { mimeType: pickMime() });
    chunks2 = [];
    recorder2.ondataavailable = (e) => { if (e.data.size) chunks2.push(e.data); };
    recorder2.start(1000);
    Transitions.recIndicator(true);
    return true;
  }

  function stopVideo2() {
    return new Promise((resolve) => {
      if (!recorder2) return resolve(null);
      recorder2.onstop = () => {
        const blob = new Blob(chunks2, { type: pickMime() });
        stream2.getTracks().forEach(t => t.stop());
        recorder2 = null; stream2 = null;
        Transitions.recIndicator(false);
        resolve(blob);
      };
      recorder2.stop();
    });
  }

  return { startVideo1, stopVideo1, startVideo2, stopVideo2 };
})();
