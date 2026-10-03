(async function main() {
  const stage = document.getElementById("stage");

  setTimeout(() => {
    document.getElementById("loading-overlay").classList.add("hidden");
  }, 1500);

  let state;
  try {
    state = await Session.bootstrap();
  } catch (e) {
    document.body.innerHTML = '<div style="color:#c9a961;text-align:center;padding:4rem;font-family:Cormorant Garamond,serif;font-size:1.3rem;">The magic could not reach you.<br><small style="opacity:0.6;">' + e.message + '</small></div>';
    return;
  }

  // First user gesture starts audio + BGM
  const startAudio = () => {
    Audio2.startAmbient();
    Audio2.setScene("intro", 4);
    document.removeEventListener("touchstart", startAudio);
    document.removeEventListener("click", startAudio);
  };
  document.addEventListener("touchstart", startAudio, { once: true });
  document.addEventListener("click", startAudio, { once: true });

  async function resumeFromState(s) {
    const flags = s.flags || {};
    if (s.completion.completedAt) return runEnd();
    if (s.completion.reactionCompleted) return runEnd();
    if (s.recordings.reaction.status === "UPLOADED") return runEnd();
    if (s.recordings.video1.status === "UPLOADED" && !flags.candleBlown) return runBirthdayPath(true);
    if (flags.candleBlown) return runPostCandlePath();
    if (flags.spellCast) return runAfterSpell();
    if (flags.gateOpened) return runSpellScene();
    return runIntro();
  }

  async function runIntro() {
    Audio2.setScene("intro", 3);
    await Scenes.intro();
    Audio2.setScene("gate", 2);
    await Scenes.gate();
    try { await API.setFlag(Session.id(), "gateOpened", true); } catch(e){}
    await Scenes.enterGate();
    await runSpellScene();
  }

  async function runSpellScene() {
    Audio2.setScene("spell", 2);
    const scene = await Scenes.spellPrompt();
    const trySpeech = () => Audio2.listenForWord("alohomora", 10000);
    const ok = await trySpeech();
    if (!ok) {
      await new Promise((resolve) => {
        const btn = Scenes.el("button", "magic-btn", "I Spoke It ✦");
        scene.appendChild(btn);
        btn.addEventListener("click", () => resolve(), { once: true });
      });
    }
    try { await API.setFlag(Session.id(), "spellCast", true); } catch(e){}
    Audio2.play("chime");
    await Transitions.flashWhite(2500);
    await Scenes.welcome();
    await runBirthdayPath(false);
  }

  async function runAfterSpell() {
    Audio2.setScene("welcome", 3);
    await Scenes.welcome();
    await runBirthdayPath(false);
  }

  async function runBirthdayPath(resume) {
    await Scenes.clear();

    try {
      await Camera.startVideo1();
      try { await API.startRecording(Session.id(), "video1"); } catch(e){}
    } catch (e) {
      alert("Camera access is needed for this magical experience.");
      return;
    }

    Audio2.setScene("birthday", 3);
    await Scenes.birthdayVisitor();

    Audio2.setScene("candle", 2);
    await Scenes.cakeScene();

    const blown = await Promise.race([
      Audio2.listenForBlow(9000),
      new Promise((resolve) => {
        const btn = Scenes.el("button", "magic-btn", "I Blew It ✨");
        btn.style.marginTop = "2rem";
        stage.appendChild(btn);
        btn.addEventListener("click", () => resolve(true), { once: true });
      }),
    ]);

    Audio2.play("whoosh");
    await Scenes.wait(500);
    Audio2.play("sparkle");

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

    try {
      await Camera.startVideo2();
      try { await API.startRecording(Session.id(), "reaction"); } catch(e){}
    } catch (e) {
      console.warn("Reaction camera failed", e);
    }

    await runPostCandlePath();
  }

  async function runPostCandlePath() {
    Audio2.setScene("confetti", 3);
    await Scenes.confettiTransition();
    await runWall();
  }

  async function runWall() {
    Audio2.setScene("wall", 2);
    await Scenes.wallScene();
    try { await API.setFlag(Session.id(), "wallOpened", true); } catch(e){}
    await Transitions.flashWhite(2500);
    await runAlley();
  }

  async function runAlley() {
    Audio2.setScene("alley", 3);
    await Scenes.alleyScene();
    await runTicket();
  }

  async function runTicket() {
    Audio2.setScene("alley", 2);
    await Scenes.ticketScene();
    await runTrain();
  }

  async function runTrain() {
    Audio2.setScene("train", 2);
    await Scenes.trainScene();
    await runCastle();
  }

  async function runCastle() {
    Audio2.setScene("castle", 2);
    await Scenes.castleScene();
    await runHat();
  }

  async function runHat() {
    Audio2.setScene("hat", 2);
    await Scenes.hatScene();
    try { await API.setFlag(Session.id(), "hatSorted", true); } catch(e){}
    await runQuestHub();
  }

  async function runQuestHub() {
    Audio2.setScene("levels", 2);
    let s = await Session.refresh();
    while (true) {
      s = await Session.refresh();
      const nextLevel = s.quest.unlockedLevels.find(
        (l) => !s.quest.answers[String(l)]
      );
      if (!nextLevel) break;
      await Scenes.questHub(s);
      const lvl = await new Promise((res) => { window.__levelResolve = res; });
      await Scenes.levelScene(lvl);
      await Session.refresh();
    }
    await runFinale();
  }

  async function runFinale() {
    Audio2.setScene("finale", 3);
    await Scenes.finaleReveal();
    Audio2.setScene("chest", 2);
    await Scenes.chestScene();
    await runFinalVideo();
  }

  async function runFinalVideo() {
    await Session.refresh();
    const url = "YOUR_BIRTHDAY_VIDEO_URL_HERE";
    await Scenes.finalVideo(url);
    await Scenes.finalCakeButton();

    try { await API.stopRecording(Session.id(), "reaction"); } catch(e){}
    const blob2 = await Camera.stopVideo2();
    if (blob2) {
      try {
        await API.uploadRecording(Session.id(), "reaction", blob2);
      } catch (e) {
        try { await API.uploadRecording(Session.id(), "reaction", blob2); } catch(e2){}
      }
    }
    await runEnd();
  }

  async function runEnd() {
    Audio2.setScene("end", 4);
    await Scenes.endScreen();
  }

  await resumeFromState(state);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) Session.refresh().catch(()=>{});
  });
})();
