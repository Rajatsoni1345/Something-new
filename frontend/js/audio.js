/* ============================================================
   CINEMATIC AUDIO SYSTEM — Continuous BGM + SFX
   Everything synthesized via Web Audio. No external files.
   ============================================================ */

const Audio2 = (() => {
  let ctx = null;
  let master = null;
  let reverb = null;
  let layers = {};
  let started = false;
  let currentScene = "intro";

  function ensureCtx() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      master = ctx.createGain();
      master.gain.value = 0.65;
      master.connect(ctx.destination);

      // Cathedral-style reverb
      reverb = ctx.createConvolver();
      const rate = ctx.sampleRate;
      const length = rate * 4;
      const impulse = ctx.createBuffer(2, length, rate);
      for (let ch = 0; ch < 2; ch++) {
        const data = impulse.getChannelData(ch);
        for (let i = 0; i < length; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.2);
        }
      }
      reverb.buffer = impulse;
      const revGain = ctx.createGain();
      revGain.gain.value = 0.35;
      reverb.connect(revGain).connect(master);
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  // ============ LAYER BUILDERS ============
  function makeDrone(freq, type) {
    const c = ensureCtx();
    const osc = c.createOscillator();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    const g = c.createGain();
    g.gain.value = 0;
    osc.connect(g);
    g.connect(master);
    g.connect(reverb);
    osc.start();
    return { osc, gain: g };
  }

  function makePad(freqs) {
    const c = ensureCtx();
    const group = c.createGain();
    group.gain.value = 0;
    group.connect(master);
    group.connect(reverb);
    const oscs = [];
    freqs.forEach(f => {
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.value = f;
      const g = c.createGain();
      g.gain.value = 1 / freqs.length;
      osc.connect(g).connect(group);
      osc.start();
      oscs.push(osc);
    });
    return { oscs, gain: group };
  }

  function makeNoise(filterFreq, Q) {
    const c = ensureCtx();
    const bufSize = 2 * c.sampleRate;
    const buf = c.createBuffer(1, bufSize, c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1) * 0.3;
    const src = c.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    const filt = c.createBiquadFilter();
    filt.type = "bandpass";
    filt.frequency.value = filterFreq || 800;
    filt.Q.value = Q || 0.8;
    const g = c.createGain();
    g.gain.value = 0;
    src.connect(filt).connect(g).connect(master);
    src.start();
    return { src, gain: g, filt };
  }

  function fadeTo(node, target, dur) {
    if (!node || !node.gain) return;
    const now = ctx.currentTime;
    node.gain.cancelScheduledValues(now);
    node.gain.setValueAtTime(node.gain.value, now);
    node.gain.linearRampToValueAtTime(target, now + dur);
  }

  // ============ START BGM ============
  function startAmbient() {
    if (started) return;
    started = true;
    ensureCtx();
    layers.droneLow  = makeDrone(55, "sine");
    layers.droneHigh = makeDrone(110, "sine");
    layers.padWarm   = makePad([220, 277.18, 329.63, 415.30]); // A major 7
    layers.padDark   = makePad([110, 130.81, 155.56, 196.00]); // A minor-ish
    layers.noise     = makeNoise(200, 0.4);
    setScene("intro", 4);
  }

  function setScene(name, dur) {
    if (!started) return;
    dur = dur || 3;
    currentScene = name;

    const mixes = {
      intro:    { dL: 0.16, dH: 0.07, pW: 0,    pD: 0.06, n: 0.02 },
      gate:     { dL: 0.22, dH: 0.11, pW: 0,    pD: 0.09, n: 0.04 },
      storm:    { dL: 0.24, dH: 0.12, pW: 0,    pD: 0.12, n: 0.08 },
      cake:     { dL: 0.08, dH: 0.06, pW: 0.12, pD: 0.03, n: 0.01 },
      confetti: { dL: 0.06, dH: 0.05, pW: 0.18, pD: 0,    n: 0.02 },
      alley:    { dL: 0.10, dH: 0.09, pW: 0.10, pD: 0.05, n: 0.03 },
      train:    { dL: 0.15, dH: 0.11, pW: 0.04, pD: 0.10, n: 0.06 },
      castle:   { dL: 0.12, dH: 0.09, pW: 0.12, pD: 0.06, n: 0.02 },
      hat:      { dL: 0.10, dH: 0.07, pW: 0.09, pD: 0.07, n: 0.01 },
      levels:   { dL: 0.14, dH: 0.09, pW: 0.05, pD: 0.09, n: 0.02 },
      finale:   { dL: 0.10, dH: 0.07, pW: 0.16, pD: 0.05, n: 0.01 },
      video:    { dL: 0.06, dH: 0.04, pW: 0.08, pD: 0.04, n: 0.01 },
      end:      { dL: 0.08, dH: 0.05, pW: 0.07, pD: 0.09, n: 0.01 },
    };
    const m = mixes[name] || mixes.intro;
    fadeTo(layers.droneLow, m.dL, dur);
    fadeTo(layers.droneHigh, m.dH, dur);
    fadeTo(layers.padWarm, m.pW, dur);
    fadeTo(layers.padDark, m.pD, dur);
    fadeTo(layers.noise, m.n, dur);
  }

  // ============ SFX ============
  function play(type) {
    const c = ensureCtx();
    const now = c.currentTime;

    if (type === "knock") {
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(150, now);
      osc.frequency.exponentialRampToValueAtTime(60, now + 0.15);
      const g = c.createGain();
      g.gain.setValueAtTime(0.6, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(g).connect(master);
      g.connect(reverb);
      osc.start(now); osc.stop(now + 0.5);

    } else if (type === "chime") {
      [880, 1320, 1760].forEach((f, i) => {
        const o = c.createOscillator();
        o.type = "sine";
        o.frequency.value = f;
        const g = c.createGain();
        const t = now + i * 0.08;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(0.09 - i * 0.02, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, t + 1.2);
        o.connect(g).connect(master);
        g.connect(reverb);
        o.start(t); o.stop(t + 1.3);
      });

    } else if (type === "boom") {
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(95, now);
      osc.frequency.exponentialRampToValueAtTime(28, now + 1.1);
      const g = c.createGain();
      g.gain.setValueAtTime(0.75, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 1.4);
      osc.connect(g).connect(master);
      osc.start(now); osc.stop(now + 1.5);

    } else if (type === "sparkle") {
      const osc = c.createOscillator();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(1800, now);
      osc.frequency.exponentialRampToValueAtTime(3200, now + 0.4);
      const g = c.createGain();
      g.gain.setValueAtTime(0.07, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
      osc.connect(g).connect(master);
      g.connect(reverb);
      osc.start(now); osc.stop(now + 0.8);

    } else if (type === "wrong") {
      [140, 148].forEach(f => {
        const o = c.createOscillator();
        o.type = "sawtooth";
        o.frequency.setValueAtTime(f, now);
        o.frequency.exponentialRampToValueAtTime(f * 0.6, now + 0.5);
        const g = c.createGain();
        g.gain.setValueAtTime(0.12, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
        o.connect(g).connect(master);
        o.start(now); o.stop(now + 0.8);
      });

    } else if (type === "whoosh") {
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 0.6, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 1.5);
      n.buffer = buf;
      const f = c.createBiquadFilter();
      f.type = "bandpass";
      f.frequency.setValueAtTime(700, now);
      f.frequency.exponentialRampToValueAtTime(220, now + 0.5);
      f.Q.value = 1.5;
      const g = c.createGain();
      g.gain.setValueAtTime(0.35, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
      n.connect(f).connect(g).connect(master);
      n.start(now); n.stop(now + 0.7);

    } else if (type === "thunder") {
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 1.4, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 2);
      n.buffer = buf;
      const f = c.createBiquadFilter();
      f.type = "lowpass";
      f.frequency.value = 180;
      const g = c.createGain();
      g.gain.setValueAtTime(0.35, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 1.4);
      n.connect(f).connect(g).connect(master);
      n.start(now); n.stop(now + 1.4);

    } else if (type === "train") {
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 3, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (0.5 + 0.5 * Math.sin(i * 0.0004)) * Math.pow(1 - i / d.length, 0.8);
      n.buffer = buf;
      const f = c.createBiquadFilter();
      f.type = "lowpass";
      f.frequency.value = 400;
      const g = c.createGain();
      g.gain.setValueAtTime(0.15, now);
      g.gain.linearRampToValueAtTime(0.25, now + 0.5);
      g.gain.exponentialRampToValueAtTime(0.001, now + 3);
      n.connect(f).connect(g).connect(master);
      n.start(now); n.stop(now + 3);
    }
  }

  // ============ VOICE DETECTION (Lumos) ============
  function listenForWord(targetWord, timeoutMs) {
    timeoutMs = timeoutMs || 10000;
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

  // ============ BLOW DETECTION (Candle) ============
  function listenForBlow(durationMs) {
    durationMs = durationMs || 10000;
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
        let hits = 0;
        const check = () => {
          analyser.getByteFrequencyData(buf);
          let sum = 0;
          for (let i = 1; i < 12; i++) sum += buf[i];
          const avg = sum / 11;
          if (avg > 45) hits++; else hits = Math.max(0, hits - 1);
          if (hits >= 2) {
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

  return { startAmbient, setScene, play, listenForWord, listenForBlow, ensureCtx };
})();
