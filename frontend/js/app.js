(async function main() {
  const stage = document.getElementById("stage");

  setTimeout(() => {
    document.getElementById("loading-overlay").classList.add("hidden");
  }, 800);

  let state;
  try {
    state = await Session.bootstrap();
  } catch (e) {
    document.body.innerHTML = '<div style="color:#d4af37;text-align:center;padding:4rem;font-family:Cormorant Garamond,serif;">The magic could not reach you.<br><small>' + e.message + '</small></div>';
    return;
  }

  const startAudio = () => {
    Audio2.startAmbient();
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
    await Scenes.intro();
    await Scenes.gate();
    try { await API.setFlag(Session.id(), "gateOpened", true); } catch(e){}
    await Scenes.enterGate();
    await runSpellScene();
  }

  async function runSpellScene() {
    const scene = await Scenes.spellPrompt();
    const trySpeech = () => Audio2.listenForWord("alohomora", 8000);
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
    await Transitions.flashWhite(1800);
    await Scenes.welcome();
    await runBirthdayPath(false);
  }

  async function runAfterSpell() {
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

    await Scenes.birthdayVisitor();
    await Scenes.cakeScene();

    const blown = await Promise.race([
      Audio2.listenForBlow(7000),
      new Promise((resolve) => {
        const btn = Scenes.el("button", "magic-btn", "I Blew It ✨");
        btn.style.marginTop = "2rem";
        stage.appendChild(btn);
        btn.addEventListener("click", () => resolve(true), { once: true });
      }),
    ]);

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
    await Scenes.confettiTransition();
    await runWall();
  }

  async function runWall() {
    await Scenes.wallScene();
    try { await API.setFlag(Session.id(), "wallOpened", true); } catch(e){}
    await Transitions.flashWhite(1800);
    await runAlley();
  }

  async function runAlley() {
    await Scenes.alleyScene();
    await runTicket();
  }

  async function runTicket() {
    await Scenes.ticketScene();
    await runTrain();
  }

  async function runTrain() {
    await Scenes.trainScene();
    await runCastle();
  }

  async function runCastle() {
    await Scenes.castleScene();
    await runHat();
  }

  async function runHat() {
    await Scenes.hatScene();
    try { await API.setFlag(Session.id(), "hatSorted", true); } catch(e){}
    await runQuestHub();
  }

  async function runQuestHub() {
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
    await Scenes.finaleReveal();
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
    await Scenes.endScene ? Scenes.endScreen() : Scenes.endScreen();
  }

  await resumeFromState(state);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) Session.refresh().catch(()=>{});
  });
})();
