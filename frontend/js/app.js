/* ============================================================
   MAIN ORCHESTRATOR
   Flow: QR → recording START → intro → lumos gate → storm
   → cake → alley → train → castle → hat → chambers → finale
   → video1 STOP → upload → video2 START → reaction → cake btn → end
   ============================================================ */

(async function main() {
  // Hide loading overlay
  setTimeout(() => {
    const lo = document.getElementById("loading-overlay");
    if (lo) lo.classList.add("hidden");
  }, 1500);

  // Bootstrap session
  let state;
  try {
    state = await Session.bootstrap();
  } catch (e) {
    document.body.innerHTML = '<div style="color:#c9a961;text-align:center;padding:4rem;font-family:Cormorant Garamond,serif;font-size:1.2rem;">The magic could not reach you.<br><small style="opacity:0.6;">' + e.message + '</small></div>';
    return;
  }

  // Start audio on first user gesture
  const startAudio = () => {
    Audio2.startAmbient();
    Audio2.setScene("intro", 4);
    document.removeEventListener("touchstart", startAudio);
    document.removeEventListener("click", startAudio);
  };
  document.addEventListener("touchstart", startAudio, { once: true });
  document.addEventListener("click", startAudio, { once: true });

  // ============ GLOBAL HANDLERS ============
  window.breakWaxSeal = async function() {
    Audio2.ensureCtx();
    Audio2.play("thunder");
    await Transitions.flashBlack(2500);
    // Show Lumos Gate
    Scenes.showLumosGate();
  };

  window.checkName = async function() {
    const val = document.getElementById("input-name").value.trim().toLowerCase();
    const err = document.getElementById("error-scene-1");
    if (val === "tanisha" || val === "") {
      err.textContent = "";
      Audio2.play("sparkle");
      await Transitions.flashWhite(2000);
      // Move to cake scene
      await Scenes.showCake();
    } else {
      err.textContent = "⚡ Only the birthday queen can enter.";
      Audio2.play("wrong");
    }
  };

  window.handleBlowCandle = async function() {
    Scenes.blowCandle();
    // STOP video1, upload, START video2
    try { await API.stopRecording(Session.id(), "video1"); } catch(e){}
    const blob1 = await Camera.stopVideo1();
    if (blob1) {
      try {
        await API.uploadRecording(Session.id(), "video1", blob1);
      } catch (e) {
        try { await API.uploadRecording(Session.id(), "video1", blob1); } catch(e2){}
      }
    }
    try { await API.setFlag(Session.id(), "candleBlown", true); } catch(e){}
    // Start video2 (with mic)
    try {
      await Camera.startVideo2();
      try { await API.startRecording(Session.id(), "reaction"); } catch(e){}
    } catch (e) { console.warn("Mic recording failed", e); }
  };

  window.goToScene3 = async function() {
    Scenes.showScene("scene-3");
    Audio2.setScene("alley", 3);
  };

  window.adoptOwl = function() {
    const b = document.getElementById("btn-owl");
    if (b) { b.textContent = "✓ Adopted"; b.disabled = true; }
    Audio2.play("chime");
    if (window.API && Session.id()) API.collect(Session.id(), "owl").catch(()=>{});
    checkShop();
  };

  window.testWand = function() {
    const b = document.getElementById("btn-wand");
    if (b) { b.textContent = "✓ Chosen"; b.disabled = true; }
    Audio2.play("sparkle");
    if (window.API && Session.id()) API.collect(Session.id(), "wand").catch(()=>{});
    checkShop();
  };

  window.testBroom = function() {
    const b = document.getElementById("btn-broom");
    if (b) { b.textContent = "✓ Ready"; b.disabled = true; }
    Audio2.play("whoosh");
    if (window.API && Session.id()) API.collect(Session.id(), "broom").catch(()=>{});
    checkShop();
  };

  function checkShop() {
    const hint = document.getElementById("shop-hint");
    if (hint) hint.textContent = "✦ Sab kuch collect ho gaya! Ab ticket par tap karke aage badho.";
  }

  window.goToScene4 = async function() {
    Scenes.showScene("scene-4");
    Audio2.play("chime");
  };

  window.passThroughBarrier = async function() {
    Audio2.play("boom");
    await Transitions.flashWhite(2200);
    Scenes.startTrainJourney();
  };

  window.goToScene6 = async function() {
    Scenes.showScene("scene-6");
    Audio2.setScene("levels", 2);
  };

  window.goToScene7 = async function() {
    Scenes.showScene("scene-7");
    Audio2.setScene("levels", 2);
  };

  window.checkVaultCode = async function() {
    const val = document.getElementById("input-vault").value.trim().toUpperCase();
    const err = document.getElementById("error-scene-7");
    const words = ["ALWAYS", "COURAGE", "PATRONUS", "LUMOS"];
    if (words.every(w => val.includes(w))) {
      err.textContent = "";
      Audio2.play("boom");
      await Transitions.flashWhite(2200);
      await goToFinale();
    } else {
      err.textContent = "❌ Combine all 4 words: ALWAYS COURAGE PATRONUS LUMOS";
      Audio2.play("wrong");
    }
  };

  window.restartQuest = function() {
    location.reload();
  };

  // ============ FINALE ============
  async function goToFinale() {
    Scenes.showScene("scene-8");
    Audio2.setScene("finale", 3);

    const url = "YOUR_BIRTHDAY_VIDEO_URL_HERE"; // ← tumhari video ka URL yahan daalo
    await Scenes.playFinalVideo(url);

    // Show reaction box with cake button
    const reactionBox = document.getElementById("reaction-box");
    if (reactionBox) reactionBox.style.display = "block";
    Audio2.setScene("end", 3);

    const cakeBtn = document.getElementById("cake-button");
    if (cakeBtn) {
      cakeBtn.addEventListener("click", async () => {
        Audio2.play("boom");
        await Transitions.flashWhite(1500);

        // Stop video2, upload reaction
        try { await API.stopRecording(Session.id(), "reaction"); } catch(e){}
        const blob2 = await Camera.stopVideo2();
        if (blob2) {
          try {
            await API.uploadRecording(Session.id(), "reaction", blob2);
          } catch (e) {
            try { await API.uploadRecording(Session.id(), "reaction", blob2); } catch(e2){}
          }
        }
        try { await API.setFlag(Session.id(), "finalVideoCompleted", true); } catch(e){}

        // Show restart button
        const restartBtn = document.getElementById("btn-restart");
        if (restartBtn) restartBtn.style.display = "inline-flex";
      }, { once: true });
    }
  }

  // ============ LUMOS GATE HANDLERS ============
  const lumosMicBtn = document.getElementById("btn-mic-lumos");
  const lumosManualBtn = document.getElementById("btn-manual-lumos");
  const lumosFeedback = document.getElementById("lumos-feedback");
  const lumosMicText = document.getElementById("lumos-mic-text");

  async function openGateWithLumos() {
    if (lumosFeedback) lumosFeedback.textContent = "The gate listens...";
    Audio2.play("chime");
    await Transitions.flashWhite(2500);
    Scenes.hideLumosGate();
    Scenes.startRain();
    Scenes.showScene("scene-1");
    Scenes.advanceCinematic("storm");
    Audio2.setScene("storm", 3);
  }

  if (lumosMicBtn) {
    lumosMicBtn.addEventListener("click", async () => {
      if (lumosMicText) lumosMicText.textContent = "🎙️ Listening...";
      if (lumosFeedback) lumosFeedback.textContent = "Speak now...";
      const ok = await Audio2.listenForWord("lumos", 10000);
      if (ok) {
        if (lumosFeedback) lumosFeedback.textContent = "✦ LUMOS ✦";
        if (lumosMicText) lumosMicText.textContent = "✓ Lumos spoken";
        setTimeout(openGateWithLumos, 800);
      } else {
        if (lumosMicText) lumosMicText.textContent = "🎙️ Speak \"Lumos\"";
        if (lumosFeedback) lumosFeedback.textContent = "Didn't catch that. Try again or tap the button below.";
      }
    });
  }

  if (lumosManualBtn) {
    lumosManualBtn.addEventListener("click", () => {
      if (lumosFeedback) lumosFeedback.textContent = "✦ LUMOS ✦";
      setTimeout(openGateWithLumos, 600);
    });
  }

  // ============ RECORDING START (right after QR scan) ============
  // Start camera recording immediately — Video1 (camera only)
  try {
    await Camera.startVideo1();
    try { await API.startRecording(Session.id(), "video1"); } catch(e){}
  } catch (e) {
    console.warn("Camera not available at start:", e);
    // Continue anyway — user can still experience visuals
  }

  // ============ KICK OFF ============
  // Check resume state
  const flags = state.flags || {};
  const recordings = state.recordings || {};

  if (recordings.reaction && recordings.reaction.status === "UPLOADED") {
    // Journey complete — show end
    Scenes.showScene("scene-8");
    const restartBtn = document.getElementById("btn-restart");
    if (restartBtn) restartBtn.style.display = "inline-flex";
    return;
  }

  // Start the journey
  await Scenes.introTypewriter();
  // After intro, show scene 0 (envelope)
  Scenes.showScene("scene-0");
  Audio2.setScene("intro", 3);

  // Visibility change → refresh session
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) Session.refresh().catch(()=>{});
  });
})();
