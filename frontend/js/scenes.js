const Scenes = (() => {
  const stage = () => document.getElementById("stage");

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html) e.innerHTML = html;
    return e;
  }

  function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

  async function typeText(container, text, speed) {
    speed = speed || 60;
    return new Promise((resolve) => {
      container.innerHTML = "";
      let i = 0;
      const cursor = el("span", "cursor");
      container.appendChild(cursor);
      const timer = setInterval(() => {
        if (i >= text.length) {
          clearInterval(timer);
          cursor.remove();
          resolve();
          return;
        }
        cursor.insertAdjacentText("beforebegin", text[i++]);
      }, speed);
    });
  }

  function showScene(id) {
    document.querySelectorAll(".scene").forEach(s => {
      s.classList.remove("active");
      s.style.display = "none";
    });
    const target = document.getElementById(id);
    if (target) {
      target.style.display = "flex";
      setTimeout(() => target.classList.add("active"), 20);
    }
  }

  // ============ INTRO TYPEWRITER (Black screen 3-4 messages) ============
  async function introTypewriter() {
    const overlay = el("div", "intro-typewriter");
    const textEl = el("div", "intro-typewriter-text");
    overlay.appendChild(textEl);
    document.body.appendChild(overlay);

    const lines = [
      "Some stories are written...",
      "Some are remembered...",
      "And some... are meant to be discovered.",
      "Tonight, a little magic has been waiting for you.",
      "TANISHA",
    ];

    for (let i = 0; i < lines.length; i++) {
      textEl.innerHTML = "";
      if (i === 4) {
        // Name reveal — letter by letter
        const nameWrap = el("div", "letter-reveal");
        nameWrap.style.fontFamily = "'Cinzel Decorative', serif";
        nameWrap.style.fontSize = "clamp(2rem, 10vw, 4rem)";
        nameWrap.style.letterSpacing = "0.3em";
        nameWrap.style.color = "#e8c87a";
        nameWrap.style.textShadow = "0 0 30px rgba(232,200,122,0.8)";
        [...lines[i]].forEach((ch, j) => {
          const s = document.createElement("span");
          s.textContent = ch;
          s.style.animationDelay = (j * 0.15) + "s";
          nameWrap.appendChild(s);
        });
        textEl.appendChild(nameWrap);
        Audio2.play("chime");
        await wait(5000);
      } else {
        await typeText(textEl, lines[i], 65);
        await wait(2000);
      }
    }

    overlay.style.transition = "opacity 2s ease";
    overlay.style.opacity = "0";
    await wait(2000);
    overlay.remove();
  }

  // ============ LUMOS GATE ============
  function showLumosGate() {
    const gate = document.getElementById("lumos-gate");
    if (gate) gate.classList.add("active");
    Audio2.setScene("gate", 3);
  }

  function hideLumosGate() {
    const gate = document.getElementById("lumos-gate");
    if (gate) gate.classList.remove("active");
  }

  // ============ SCENE 1 · STORM ============
  function startRain() {
    const container = document.getElementById("rain-container");
    if (!container) return;
    for (let i = 0; i < 60; i++) {
      const drop = document.createElement("div");
      drop.className = "rain-drop";
      drop.style.left = Math.random() * 100 + "%";
      drop.style.animationDelay = (Math.random() * 1) + "s";
      drop.style.animationDuration = (0.7 + Math.random() * 0.6) + "s";
      container.appendChild(drop);
    }
  }

  function advanceCinematic(phase) {
    ["storm", "knocking", "crash", "visitor", "verify"].forEach(p => {
      const el = document.getElementById("phase-" + p);
      if (el) el.style.display = "none";
    });
    const target = document.getElementById("phase-" + phase);
    if (target) target.style.display = "flex";

    if (phase === "knocking") {
      Audio2.play("knock");
      setTimeout(() => Audio2.play("knock"), 500);
      setTimeout(() => Audio2.play("knock"), 1000);
    } else if (phase === "crash") {
      Audio2.play("boom");
      const scene = document.getElementById("scene-1");
      if (scene) {
        scene.classList.add("shake");
        setTimeout(() => scene.classList.remove("shake"), 900);
      }
    } else if (phase === "visitor") {
      Audio2.play("chime");
    }
  }

  // ============ CAKE ============
  async function showCake() {
    Audio2.setScene("cake", 3);
    showScene("scene-2");
    // Keeper typewriter message
    await wait(500);
    const msg = "Tanisha... main tumhara hi wait kar raha tha. Kitni badi ho gayi ho. Aur dekho — yeh special birthday cake main tumhare liye khud bana kar laya hoon. Chalo, ab candle blow karo aur wish maango!";
    await typeText(document.getElementById("keeper-typewriter"), msg, 50);
  }

  function blowCandle() {
    const flame = document.getElementById("candle-flame");
    const smoke = document.getElementById("candle-smoke");
    const blowBox = document.getElementById("candle-blow-box");
    const celebration = document.getElementById("candle-celebration");
    const nextBtn = document.getElementById("btn-next-scene3");

    if (flame) flame.style.display = "none";
    if (smoke) smoke.style.display = "block";
    if (blowBox) blowBox.style.display = "none";
    if (celebration) celebration.style.display = "block";
    if (nextBtn) nextBtn.style.display = "inline-flex";

    Audio2.play("whoosh");
    setTimeout(() => Audio2.play("chime"), 300);
    setTimeout(() => Audio2.play("sparkle"), 600);

    // Confetti
    Transitions.confetti(150, 8000);
    Audio2.setScene("confetti", 3);
  }

  // ============ ALLEY ============
  async function goToAlley() {
    Audio2.setScene("alley", 3);
    showScene("scene-3");
  }

  // ============ TRAIN ============
  async function startTrainJourney() {
    showScene("scene-4");
    Audio2.setScene("train", 3);
    Audio2.play("train");
    await wait(4000);
    // Auto-advance to castle
    showScene("scene-5");
    Audio2.setScene("castle", 3);
    await wait(2000);
    // Hat scene
    const msg = "Hmm... bohot mushkil faisla hai. Dimag me aisi tezi jo har paheli suljha le, aur dil me aisi gehrai jo sabka khayal rakhe. Bilkul sahi — yeh to House of the Brave ki rani hai!";
    await typeText(document.getElementById("hat-typewriter"), msg, 45);
    const btn = document.getElementById("btn-hat-next");
    if (btn) btn.style.display = "inline-flex";
  }

  // ============ CHAMBERS / LEVELS ============
  const QUEST_DATA = {
    1: { title: "Chamber of Eternal Laughter", story: "Yahan tumhari muskaan ki chamak ka pehla hissa qaid hai...", riddle: "The deepest truth of a heart that waited — 'After all this time?'", answer: "always", reward: "ALWAYS" },
    2: { title: "Chamber of Indomitable Will", story: "Gryffindor ki veerta aur tumhara jazba yahan pariksha leta hai...", riddle: "Mushkil se mushkil toofan me bhi tumhara sabse bada hathiyar kya hai?", answer: "courage", reward: "COURAGE" },
    3: { title: "Chamber of Starlight Radiance", story: "Andhere ko bhagane wali roshni yahan hai...", riddle: "Dementors ko bhagane wala sabse khushnuma mantra ka naam?", answer: "patronus", reward: "PATRONUS" },
    4: { title: "The Sanctuary of Pure Light", story: "Tumhari aankhon me wo jaadu hai jo kitabon me nahi milta...", riddle: "Andhere me roshni lane wala wand ka pehla mantra?", answer: "lumos", reward: "LUMOS" },
  };

  let unlockedLevels = [1];
  let completedLevels = [];
  let currentModalLevel = 1;

  function openLevelModal(lvl) {
    if (!unlockedLevels.includes(lvl)) return;
    currentModalLevel = lvl;
    const d = QUEST_DATA[lvl];
    document.getElementById("modal-level-num").textContent = "Chamber " + ["I","II","III","IV"][lvl-1];
    document.getElementById("modal-level-title").textContent = d.title;
    document.getElementById("modal-level-story").textContent = d.story;
    document.getElementById("modal-level-riddle").textContent = d.riddle;
    document.getElementById("modal-answer-input").value = "";
    document.getElementById("modal-error").textContent = "";
    document.getElementById("level-modal").style.display = "flex";
    Audio2.setScene("levels", 2);
  }

  function closeModal() {
    document.getElementById("level-modal").style.display = "none";
  }

  function submitLevelAnswer() {
    const inp = document.getElementById("modal-answer-input").value.trim().toLowerCase();
    const d = QUEST_DATA[currentModalLevel];
    const err = document.getElementById("modal-error");
    if (inp === d.answer) {
      closeModal();
      Audio2.play("chime");
      Transitions.flashWhite(1800);
      if (!completedLevels.includes(currentModalLevel)) {
        completedLevels.push(currentModalLevel);
        const badge = document.getElementById("badge-door-" + currentModalLevel);
        if (badge) badge.textContent = "RUNE: " + d.reward + " ✨";
      }
      if (currentModalLevel < 4 && !unlockedLevels.includes(currentModalLevel + 1)) {
        unlockedLevels.push(currentModalLevel + 1);
        const nextCard = document.getElementById("card-door-" + (currentModalLevel + 1));
        if (nextCard) nextCard.classList.add("unlocked");
      }
      if (completedLevels.length >= 4) {
        const btn = document.getElementById("btn-proceed-vault");
        if (btn) { btn.style.opacity = "1"; btn.style.pointerEvents = "auto"; }
      }
      // Backend answer submit
      if (window.API && Session.id()) {
        API.answer(Session.id(), currentModalLevel, inp).catch(()=>{});
      }
    } else {
      err.textContent = "❌ Incorrect incantation. Think deeper...";
      Audio2.play("wrong");
    }
  }

  // ============ SEALED CHAMBER ============
  function autoFillVault() {
    document.getElementById("input-vault").value = "ALWAYS COURAGE PATRONUS LUMOS";
    Audio2.play("sparkle");
  }

  // ============ FINALE VIDEO ============
  async function playFinalVideo(url) {
    const v = document.getElementById("final-video");
    if (!v) return;
    v.src = url;
    v.controls = false;
    v.autoplay = true;
    v.playsInline = true;
    Audio2.setScene("video", 2);

    return new Promise((resolve) => {
      v.addEventListener("ended", () => resolve(true), { once: true });
      v.addEventListener("error", () => resolve(true), { once: true });
      // Also timeout after 5 minutes just in case
      setTimeout(() => resolve(true), 300000);
    });
  }

  return {
    introTypewriter, showLumosGate, hideLumosGate,
    startRain, advanceCinematic,
    showCake, blowCandle,
    goToAlley, startTrainJourney,
    openLevelModal, closeModal, submitLevelAnswer, autoFillVault,
    playFinalVideo, showScene, el, typeText, wait,
  };
})();

// Global handlers (called from inline onclick in HTML)
window.advanceCinematic = Scenes.advanceCinematic;
window.openLevelModal = Scenes.openLevelModal;
window.closeModal = Scenes.closeModal;
window.submitLevelAnswer = Scenes.submitLevelAnswer;
window.autoFillVault = Scenes.autoFillVault;
