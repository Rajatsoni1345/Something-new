const Audio2 = (() => {
  let ctx = null;
  let ambientStarted = false;

  function ensureCtx() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  function startAmbient() {
    if (ambientStarted) return;
    ambientStarted = true;
    const c = ensureCtx();

    const drone = c.createOscillator();
    drone.type = "sine";
    drone.frequency.value = 55;
    const droneGain = c.createGain();
    droneGain.gain.value = 0.035;
    drone.connect(droneGain).connect(c.destination);
    drone.start();

    const shimmer = c.createOscillator();
    shimmer.type = "sine";
    shimmer.frequency.value = 660;
    const shimGain = c.createGain();
    shimGain.gain.value = 0.006;
    shimmer.connect(shimGain).connect(c.destination);
    shimmer.start();
  }

  function play(type) {
    const c = ensureCtx();
    const now = c.currentTime;
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.connect(g).connect(c.destination);

    if (type === "knock") {
      osc.type = "square"; osc.frequency.setValueAtTime(120, now);
      g.gain.setValueAtTime(0.35, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now); osc.stop(now + 0.3);
    } else if (type === "chime") {
      osc.type = "sine"; osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(1320, now + 0.5);
      g.gain.setValueAtTime(0.18, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
      osc.start(now); osc.stop(now + 0.9);
    } else if (type === "boom") {
      osc.type = "sine"; osc.frequency.setValueAtTime(80, now);
      osc.frequency.exponentialRampToValueAtTime(30, now + 0.8);
      g.gain.setValueAtTime(0.4, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 1);
      osc.start(now); osc.stop(now + 1.1);
    } else if (type === "sparkle") {
      osc.type = "triangle"; osc.frequency.setValueAtTime(1500, now);
      osc.frequency.exponentialRampToValueAtTime(2400, now + 0.3);
      g.gain.setValueAtTime(0.08, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc.start(now); osc.stop(now + 0.55);
    } else if (type === "wrong") {
      osc.type = "sawtooth"; osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(90, now + 0.4);
      g.gain.setValueAtTime(0.2, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc.start(now); osc.stop(now + 0.6);
    }
  }

  function listenForWord(targetWord, timeoutMs) {
    timeoutMs = timeoutMs || 8000;
    return new Promise((resolve) => {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) return resolve(false);
      const rec = new SR();
      rec.lang = "en-US";
      rec.interimResults = true;
      rec.continuous = false;
      let done = false;
      const t = setTimeout(() => { if (!done) { done = true; try { rec.stop(); } catch(e){} resolve(false); } }, timeoutMs);
      rec.onresult = (e) => {
        const txt = Array.from(e.results).map(r => r[0].transcript).join(" ").toLowerCase();
        if (txt.includes(targetWord.toLowerCase())) {
          done = true; clearTimeout(t);
          try { rec.stop(); } catch(e){}
          resolve(true);
        }
      };
      rec.onerror = () => { if (!done) { done = true; clearTimeout(t); resolve(false); } };
      rec.onend = () => { if (!done) { done = true; clearTimeout(t); resolve(false); } };
      try { rec.start(); } catch(e) { resolve(false); }
    });
  }

  function listenForBlow(durationMs) {
    durationMs = durationMs || 6000;
    return new Promise(async (resolve) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const c = ensureCtx();
        const src = c.createMediaStreamSource(stream);
        const analyser = c.createAnalyser();
        analyser.fftSize = 512;
        src.connect(analyser);
        const buf = new Uint8Array(analyser.frequencyBinCount);
        const start = Date.now();
        const check = () => {
          analyser.getByteFrequencyData(buf);
          let sum = 0;
          for (let i = 0; i < buf.length; i++) sum += buf[i];
          const avg = sum / buf.length;
          if (avg > 55) {
            stream.getTracks().forEach(t => t.stop());
            return resolve(true);
          }
          if (Date.now() - start > durationMs) {
            stream.getTracks().forEach(t => t.stop());
            return resolve(false);
          }
          requestAnimationFrame(check);
        };
        check();
      } catch (e) { resolve(false); }
    });
  }

  return { startAmbient, play, listenForWord, listenForBlow, ensureCtx };
})();
