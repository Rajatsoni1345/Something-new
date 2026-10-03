/* ==========================================================
   CINEMATIC AUDIO SYSTEM - Continuous BGM + SFX
   All generated via WebAudio - no external files
   ========================================================== */

const Audio2 = (() => {
  let ctx = null;
  let masterGain = null;
  let reverbNode = null;
  let layers = {};
  let started = false;
  let currentScene = "intro";

  function ensureCtx() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      masterGain = ctx.createGain();
      masterGain.gain.value = 0.7;
      masterGain.connect(ctx.destination);

      // Reverb (cathedral) - generated impulse
      reverbNode = ctx.createConvolver();
      const rate = ctx.sampleRate;
      const length = rate * 4;
      const impulse = ctx.createBuffer(2, length, rate);
      for (let ch = 0; ch < 2; ch++) {
        const data = impulse.getChannelData(ch);
        for (let i = 0; i < length; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.2);
        }
      }
      reverbNode.buffer = impulse;
      const reverbGain = ctx.createGain();
      reverbGain.gain.value = 0.4;
      reverbNode.connect(reverbGain).connect(masterGain);
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  // ============ BGM LAYERS ============

  function createDrone(freq, gainVal, type) {
    const c = ensureCtx();
    const osc = c.createOscillator();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    const g = c.createGain();
    g.gain.value = 0;
    osc.connect(g);
    g.connect(masterGain);
    g.connect(reverbNode);
    osc.start();
    return { osc, gain: g };
  }

  function createPad(frequencies, gainVal) {
    const c = ensureCtx();
    const group = c.createGain();
    group.gain.value = 0;
    group.connect(masterGain);
    group.connect(reverbNode);
    const oscs = [];
    frequencies.forEach(f => {
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.value = f;
      const g = c.createGain();
      g.gain.value = 1 / frequencies.length;
      osc.connect(g).connect(group);
      osc.start();
      oscs.push(osc);
    });
    return { oscs, gain: group };
  }

  function createNoise() {
    const c = ensureCtx();
    const bufferSize = 2 * c.sampleRate;
    const buffer = c.createBuffer(1, bufferSize, c.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * 0.3;
    const src = c.createBufferSource();
    src.buffer = buffer;
    src.loop = true;
    const filter = c.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.value = 800;
    filter.Q.value = 0.8;
    const g = c.createGain();
    g.gain.value = 0;
    src.connect(filter).connect(g).connect(masterGain);
    src.start();
    return { src, gain: g, filter };
  }

  function fadeTo(node, target, duration) {
    if (!node || !node.gain) return;
    const now = ctx.currentTime;
    node.gain.cancelScheduledValues(now);
    node.gain.setValueAtTime(node.gain.value, now);
    node.gain.linearRampToValueAtTime(target, now + duration);
  }

  // ============ BGM CONTROL ============

  function startAmbient() {
    if (started) return;
    started = true;
    ensureCtx();

    // Base layers - always present
    layers.droneLow = createDrone(55, 0, "sine");       // 55Hz - deep
    layers.droneHigh = createDrone(110, 0, "sine");     // 110Hz harmonic
    layers.noise = createNoise();
    layers.noise.filter.frequency.value = 200;
    layers.noise.filter.Q.value = 0.3;

    // Warm pad - magical presence
    layers.padWarm = createPad([220, 277.18, 329.63], 0);   // A3 C#4 E4 (A major)
    // Dark pad - mystery
    layers.padDark = createPad([110, 130.81, 164.81], 0);   // A2 C3 E3 (A minor)

    // Initial scene
    setScene("intro", 3);
  }

  function setScene(sceneName, fadeTime) {
    if (!started) return;
    fadeTime = fadeTime || 3;
    currentScene = sceneName;

    // Reset all gains first
    const reset = (t) => {
      fadeTo(layers.droneLow, t.droneLow || 0, fadeTime);
      fadeTo(layers.droneHigh, t.droneHigh || 0, fadeTime);
      fadeTo(layers.padWarm, t.padWarm || 0, fadeTime);
      fadeTo(layers.padDark, t.padDark || 0, fadeTime);
      fadeTo(layers.noise, t.noise || 0, fadeTime);
    };

    // Scene-specific mixes
    const mixes = {
      intro:      { droneLow: 0.14, droneHigh: 0.06, padWarm: 0,    padDark: 0.05, noise: 0.02 },
      gate:       { droneLow: 0.20, droneHigh: 0.10, padWarm: 0,    padDark: 0.08, noise: 0.04 },
      spell:      { droneLow: 0.16, droneHigh: 0.10, padWarm: 0.05, padDark: 0.04, noise: 0.02 },
      welcome:    { droneLow: 0.10, droneHigh: 0.08, padWarm: 0.14, padDark: 0,    noise: 0.01 },
      birthday:   { droneLow: 0.08, droneHigh: 0.06, padWarm: 0.10, padDark: 0.03, noise: 0.01 },
      candle:     { droneLow: 0.10, droneHigh: 0.08, padWarm: 0.08, padDark: 0.05, noise: 0.02 },
      confetti:   { droneLow: 0.06, droneHigh: 0.04, padWarm: 0.16, padDark: 0,    noise: 0.02 },
      wall:       { droneLow: 0.18, droneHigh: 0.10, padWarm: 0,    padDark: 0.10, noise: 0.06 },
      alley:      { droneLow: 0.10, droneHigh: 0.08, padWarm: 0.08, padDark: 0.06, noise: 0.02 },
      train:      { droneLow: 0.14, droneHigh: 0.10, padWarm: 0.04, padDark: 0.08, noise: 0.05 },
      castle:     { droneLow: 0.12, droneHigh: 0.08, padWarm: 0.10, padDark: 0.06, noise: 0.02 },
      hat:        { droneLow: 0.10, droneHigh: 0.06, padWarm: 0.08, padDark: 0.06, noise: 0.01 },
      levels:     { droneLow: 0.14, droneHigh: 0.08, padWarm: 0.04, padDark: 0.08, noise: 0.02 },
      finale:     { droneLow: 0.10, droneHigh: 0.06, padWarm: 0.14, padDark: 0.04, noise: 0.01 },
      chest:      { droneLow: 0.14, droneHigh: 0.08, padWarm: 0.10, padDark: 0.06, noise: 0.02 },
      end:        { droneLow: 0.08, droneHigh: 0.04, padWarm: 0.06, padDark: 0.08, noise: 0.01 },
    };

    reset(mixes[sceneName] || mixes.intro);
  }

  // ============ SFX ============

  function play(type) {
    const c = ensureCtx();
    const now = c.currentTime;

    if (type === "knock") {
      // Deep wooden knock
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(60, now + 0.15);
      const g = c.createGain();
      g.gain.setValueAtTime(0.6, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(g).connect(masterGain);
      g.connect(reverbNode);
      osc.start(now); osc.stop(now + 0.5);
      // Impact noise
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 0.1, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
      n.buffer = buf;
      const nf = c.createBiquadFilter();
      nf.type = "lowpass";
      nf.frequency.value = 400;
      const ng = c.createGain();
      ng.gain.setValueAtTime(0.5, now);
      ng.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      n.connect(nf).connect(ng).connect(masterGain);
      n.start(now); n.stop(now + 0.3);

    } else if (type === "chime") {
      // Ethereal chime
      [880, 1320, 1760].forEach((f, i) => {
        const osc = c.createOscillator();
        osc.type = "sine";
        osc.frequency.value = f;
        const g = c.createGain();
        const t = now + i * 0.08;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(0.09 - i * 0.02, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, t + 1.2);
        osc.connect(g).connect(masterGain);
        g.connect(reverbNode);
        osc.start(t); osc.stop(t + 1.3);
      });

    } else if (type === "boom") {
      // Massive bass impact
      const osc = c.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(90, now);
      osc.frequency.exponentialRampToValueAtTime(28, now + 1.1);
      const g = c.createGain();
      g.gain.setValueAtTime(0.75, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 1.4);
      osc.connect(g).connect(masterGain);
      osc.start(now); osc.stop(now + 1.5);
      // Sub noise
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 0.4, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 2);
      n.buffer = buf;
      const nf = c.createBiquadFilter();
      nf.type = "lowpass";
      nf.frequency.value = 200;
      const ng = c.createGain();
      ng.gain.setValueAtTime(0.4, now);
      ng.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
      n.connect(nf).connect(ng).connect(masterGain);
      n.start(now); n.stop(now + 1.2);

    } else if (type === "sparkle") {
      // High sparkling sweep
      const osc = c.createOscillator();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(1800, now);
      osc.frequency.exponentialRampToValueAtTime(3200, now + 0.4);
      const g = c.createGain();
      g.gain.setValueAtTime(0.06, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
      osc.connect(g).connect(masterGain);
      g.connect(reverbNode);
      osc.start(now); osc.stop(now + 0.8);

    } else if (type === "wrong") {
      // Dissonant low
      [140, 148].forEach(f => {
        const osc = c.createOscillator();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(f, now);
        osc.frequency.exponentialRampToValueAtTime(f * 0.6, now + 0.5);
        const g = c.createGain();
        g.gain.setValueAtTime(0.12, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
        osc.connect(g).connect(masterGain);
        osc.start(now); osc.stop(now + 0.8);
      });

    } else if (type === "whoosh") {
      // Air whoosh (candle blow)
      const n = c.createBufferSource();
      const buf = c.createBuffer(1, c.sampleRate * 0.6, c.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 1.5);
      n.buffer = buf;
      const f = c.createBiquadFilter();
      f.type = "bandpass";
      f.frequency.setValueAtTime(600, now);
      f.frequency.exponentialRampToValueAtTime(200, now + 0.5);
      f.Q.value = 1.5;
      const g = c.createGain();
      g.gain.setValueAtTime(0.35, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
      n.connect(f).connect(g).connect(masterGain);
      n.start(now); n.stop(now + 0.7);
    }
  }

  // ============ INTERACTION DETECTION ============

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
    durationMs = durationMs || 8000;
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
          if (avg > 50) {
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
