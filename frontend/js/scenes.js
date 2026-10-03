const Scenes = (() => {
  const stage = () => document.getElementById("stage");

  function clear() { stage().innerHTML = ""; }

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html) e.innerHTML = html;
    return e;
  }

  function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

  async function typeText(container, text, speed) {
    speed = speed || 55;
    return new Promise((resolve) => {
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

  async function intro() {
    clear();
    const scene = el("div", "scene");
    const textWrap = el("div", "typed-text");
    scene.appendChild(textWrap);
    stage().appendChild(scene);

    const lines = [
      "Some stories are written...",
      "Some are remembered...",
      "And some... are meant to be discovered.",
      "Tonight, a little magic has been waiting for you.",
    ];

    for (const line of lines) {
      textWrap.innerHTML = "";
      await typeText(textWrap, line, 60);
      await wait(1500);
    }

    textWrap.innerHTML = "";
    await wait(400);
    const nameWrap = el("div", "name-reveal");
    const name = "TANISHA";
    [...name].forEach((ch, i) => {
      const s = el("span", "", ch === " " ? "&nbsp;" : ch);
      s.style.animationDelay = (i * 0.12) + "s";
      nameWrap.appendChild(s);
    });
    scene.appendChild(nameWrap);
    Audio2.play("chime");
    await wait(4500);
  }

  async function gate() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "#000";
    scene.innerHTML =
      '<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 60%, rgba(80,60,20,0.35), transparent 65%),linear-gradient(180deg, #050505 0%, #0a0805 100%);"></div>' +
      '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">' +
        '<div id="gate-doors" style="width:70vw;max-width:900px;height:85vh;display:flex;position:relative;perspective:1200px;">' +
          '<div id="gate-left" style="flex:1;height:100%;background:repeating-linear-gradient(90deg,#1a1208 0 8px,#241a0c 8px 16px,#1a1208 16px 24px),linear-gradient(180deg,#2a1e0f,#0d0805);border:2px solid rgba(212,175,55,0.35);border-right:none;box-shadow:inset -20px 0 60px rgba(0,0,0,0.95),0 0 80px rgba(0,0,0,0.9);transform-origin:left center;transition:transform 3.5s cubic-bezier(0.7,0,0.3,1);">' +
            '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#d4af37;font-size:3rem;opacity:0.6;">✦</div>' +
          '</div>' +
          '<div id="gate-right" style="flex:1;height:100%;background:repeating-linear-gradient(90deg,#1a1208 0 8px,#241a0c 8px 16px,#1a1208 16px 24px),linear-gradient(180deg,#2a1e0f,#0d0805);border:2px solid rgba(212,175,55,0.35);border-left:none;box-shadow:inset 20px 0 60px rgba(0,0,0,0.95),0 0 80px rgba(0,0,0,0.9);transform-origin:right center;transition:transform 3.5s cubic-bezier(0.7,0,0.3,1);">' +
            '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#d4af37;font-size:3rem;opacity:0.6;">✦</div>' +
          '</div>' +
        '</div>' +
      '</div>';
    stage().appendChild(scene);
    await wait(2500);
    Audio2.play("boom");
    await wait(600);
    document.getElementById("gate-left").style.transform = "rotateY(-115deg)";
    document.getElementById("gate-right").style.transform = "rotateY(115deg)";
    await wait(3500);
  }

  async function enterGate() {
    const scene = stage().querySelector(".scene");
    if (scene) await Transitions.cameraForward(scene, 4000);
    clear();
  }

  async function spellPrompt() {
    clear();
    const scene = el("div", "scene");
    const p = el("div", "caption");
    p.innerHTML = "A final spell stands between you<br>and the world beyond...";
    scene.appendChild(p);
    stage().appendChild(scene);
    await wait(3500);

    scene.innerHTML = "";
    const prompt1 = el("div", "spell-prompt", "Speak the word:<br><br>ALOHOMORA");
    scene.appendChild(prompt1);
    return scene;
  }

  async function welcome() {
    clear();
    const scene = el("div", "scene");
    const cap = el("div", "caption");
    cap.innerHTML = '<strong>THE GATE HAS OPENED</strong><br><br>Welcome, Tanisha.<br>Your magical journey begins now.';
    scene.appendChild(cap);
    stage().appendChild(scene);
    Audio2.play("chime");
    await wait(5000);
  }

  async function birthdayVisitor() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at 50% 70%, rgba(60,30,10,0.4), transparent 70%),#050403";

    const door = el("div", "", '<div style="width:220px;height:380px;background:linear-gradient(180deg,#1a0f08,#0a0603);border:3px solid rgba(212,175,55,0.3);border-radius:4px;box-shadow:0 0 60px rgba(0,0,0,0.95),inset 0 0 40px rgba(0,0,0,0.8);position:relative;transition:transform 0.6s ease;" id="bday-door"><div style="position:absolute;top:50%;right:12px;width:10px;height:10px;border-radius:50%;background:radial-gradient(circle,#d4af37,#6b4f1e);box-shadow:0 0 20px rgba(212,175,55,0.9);"></div></div>');
    scene.appendChild(door);
    stage().appendChild(scene);
    await wait(1500);

    for (let i = 0; i < 3; i++) {
      Audio2.play("knock");
      const doorEl = document.getElementById("bday-door");
      Transitions.shake(doorEl);
      await wait(800);
    }

    const doorEl = document.getElementById("bday-door");
    doorEl.style.transform = "rotateY(-100deg)";
    await wait(900);

    scene.innerHTML = "";
    const visitor = el("div", "caption");
    visitor.innerHTML = '<div style="font-size:8rem;filter:drop-shadow(0 0 40px rgba(212,175,55,0.6));">🧙‍♂️</div><br><em style="font-size:1.4em;">"Wait... where am I?"</em><br><br><em style="font-size:1.4em;">"Oh... I know this place."</em><br><br><em style="font-size:1.4em;">"It\'s Tanisha!"</em>';
    visitor.style.opacity = 0;
    visitor.style.transition = "opacity 2s ease";
    scene.appendChild(visitor);
    await wait(100);
    visitor.style.opacity = 1;
    await wait(5000);
  }

  async function cakeScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at center, rgba(60,30,10,0.5), #000 70%)";
    const cake = el("div", "cake-visual", "🎂");
    cake.id = "cake";
    scene.appendChild(cake);
    const msg = el("div", "caption", "Blow the candle...");
    msg.style.marginTop = "2rem";
    scene.appendChild(msg);
    stage().appendChild(scene);
    return scene;
  }

  async function confettiTransition() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at center, rgba(80,50,20,0.55), #000 75%)";
    const msg = el("div", "name-reveal", "");
    const text = "HAPPY BIRTHDAY";
    [...text].forEach((ch, i) => {
      const s = document.createElement("span");
      s.innerHTML = ch === " " ? "&nbsp;" : ch;
      s.style.animationDelay = (i * 0.08) + "s";
      msg.appendChild(s);
    });
    scene.appendChild(msg);
    stage().appendChild(scene);
    Transitions.confetti(140, 7000);
    Audio2.play("chime");
    await wait(6500);
  }

  async function wallScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "linear-gradient(180deg, #0a0503, #000)";
    const caption = el("div", "caption");
    caption.innerHTML = "Some doors aren't opened with keys.<br>Some are opened with belief.";
    scene.appendChild(caption);
    stage().appendChild(scene);
    await wait(4000);

    scene.innerHTML = "";
    const wall = el("div", "");
    wall.style.display = "grid";
    wall.style.gridTemplateColumns = "repeat(5, 70px)";
    wall.style.gap = "4px";
    wall.style.padding = "1rem";
    const correctSeq = [2, 7, 12];
    let tapped = [];
    for (let i = 0; i < 15; i++) {
      const b = el("div", "brick");
      b.dataset.idx = i;
      b.addEventListener("click", () => {
        if (tapped.includes(i)) return;
        if (correctSeq[tapped.length] === i) {
          b.classList.add("correct");
          tapped.push(i);
          Audio2.play("sparkle");
          if (tapped.length === 3) {
            setTimeout(() => {
              scene.style.transition = "transform 2s ease, opacity 2s ease";
              scene.style.transform = "scale(2.5)";
              scene.style.opacity = "0";
              Audio2.play("boom");
              setTimeout(() => window.__resolveWall && window.__resolveWall(), 2000);
            }, 900);
          }
        } else {
          Audio2.play("wrong");
          Transitions.shake(b);
        }
      });
      wall.appendChild(b);
    }
    scene.appendChild(wall);
    return new Promise((resolve) => { window.__resolveWall = resolve; });
  }

  async function alleyScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at 50% 30%, rgba(90,60,20,0.5), transparent 60%),linear-gradient(180deg,#0a0603,#000)";
    const cap = el("div", "caption");
    cap.innerHTML = "Before your journey continues...<br>three things are waiting for you.";
    scene.appendChild(cap);
    stage().appendChild(scene);
    await wait(3500);

    scene.innerHTML = "";
    const itemsWrap = el("div", "");
    itemsWrap.style.display = "flex";
    itemsWrap.style.gap = "1.5rem";
    itemsWrap.style.flexWrap = "wrap";
    itemsWrap.style.justifyContent = "center";

    const items = [
      { id: "owl", glyph: "🦉", label: "Owl" },
      { id: "wand", glyph: "⚡", label: "Wand" },
      { id: "broom", glyph: "🧹", label: "Broom" },
    ];

    const collected = new Set();
    items.forEach((it) => {
      const card = el("div", "");
      card.style.padding = "1.5rem";
      card.style.border = "1px solid rgba(212,175,55,0.35)";
      card.style.cursor = "pointer";
      card.style.transition = "all 0.6s ease";
      card.style.textAlign = "center";
      card.innerHTML = '<div style="font-size:3.5rem;filter:drop-shadow(0 0 25px rgba(212,175,55,0.6));">' + it.glyph + '</div><div style="margin-top:0.8rem;font-family:Cinzel,serif;letter-spacing:0.3em;color:#d4af37;font-size:0.8rem;">' + it.label + '</div>';
      card.addEventListener("click", async () => {
        if (collected.has(it.id)) return;
        collected.add(it.id);
        card.style.borderColor = "#f4d97b";
        card.style.boxShadow = "0 0 40px rgba(212,175,55,0.7)";
        card.style.transform = "scale(1.05)";
        Audio2.play("sparkle");
        try { await API.collect(Session.id(), it.id); } catch(e){}
      });
      itemsWrap.appendChild(card);
    });
    scene.appendChild(itemsWrap);

    return new Promise((resolve) => {
      const check = setInterval(() => {
        if (collected.size === 3) {
          clearInterval(check);
          setTimeout(resolve, 1200);
        }
      }, 500);
    });
  }

  async function ticketScene() {
    clear();
    const scene = el("div", "scene");
    const ticket = el("div", "");
    ticket.innerHTML = '<div style="background:linear-gradient(135deg,#2a1e0f,#4a3520);border:1px solid rgba(212,175,55,0.5);padding:2rem 3rem;border-radius:4px;box-shadow:0 0 60px rgba(212,175,55,0.4),inset 0 0 30px rgba(0,0,0,0.6);font-family:Cinzel,serif;letter-spacing:0.25em;color:#e8e0cf;text-align:center;transform:translateY(100vh);transition:transform 2.5s cubic-bezier(0.6,0,0.4,1);" id="ticket"><div style="color:#d4af37;font-size:0.75rem;">MAGICAL EXPRESS</div><div style="font-size:1.4rem;margin:1rem 0;">PLATFORM 9¾</div><div style="font-size:0.85rem;opacity:0.75;">Passenger</div><div style="font-size:1.6rem;color:#f4d97b;margin-top:0.4rem;">TANISHA</div></div>';
    scene.appendChild(ticket);
    stage().appendChild(scene);
    await wait(200);
    document.getElementById("ticket").style.transform = "translateY(0)";
    await wait(3500);

    const btn = el("button", "magic-btn", "Take the ticket");
    btn.addEventListener("click", async () => {
      try { await API.setFlag(Session.id(), "ticketCollected", true); } catch(e){}
      scene.innerHTML = "";
      Transitions.flashWhite(1800);
    });
    scene.appendChild(btn);
  }

  async function trainScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "linear-gradient(180deg, #050608, #0a0810)";
    scene.innerHTML = '<div style="position:absolute;inset:0;overflow:hidden;"><div id="train" style="position:absolute;bottom:30%;left:100%;font-size:6rem;filter:drop-shadow(0 0 30px rgba(212,175,55,0.5));">🚂</div></div><div class="fog"></div>';
    stage().appendChild(scene);
    Audio2.play("boom");
    const t = document.getElementById("train");
    t.style.transition = "left 6s linear";
    requestAnimationFrame(() => { t.style.left = "-30%"; });
    await wait(6500);
  }

  async function castleScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at 50% 90%, rgba(60,40,20,0.6), transparent 60%),linear-gradient(180deg,#05070d,#0a0a14 70%,#0c0a14)";
    scene.innerHTML = '<div style="font-size:10rem;filter:drop-shadow(0 0 50px rgba(212,175,55,0.5));">🏰</div><div class="caption" style="margin-top:1.5rem;">A castle stirs in the dark.</div>';
    stage().appendChild(scene);
    Audio2.play("chime");
    await wait(5000);
  }

  async function hatScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at center, rgba(50,30,10,0.6), #000 75%)";
    const hat = el("div", "", '<div style="font-size:8rem;filter:drop-shadow(0 0 40px rgba(120,80,30,0.9));">🎩</div>');
    scene.appendChild(hat);
    const caption = el("div", "caption");
    caption.style.marginTop = "2rem";
    scene.appendChild(caption);
    stage().appendChild(scene);

    const lines = [
      "<em>Hmm... interesting...</em>",
      "You care deeply.",
      "You remember the little things.",
      "You stay when others leave.",
      "And perhaps most importantly...",
      "you make people feel at home.",
    ];

    for (const line of lines) {
      caption.innerHTML = "";
      await typeText(caption, "", 1);
      caption.innerHTML = line;
      Audio2.play("sparkle");
      await wait(2800);
    }

    caption.innerHTML = "";
    const house = el("div", "name-reveal", "");
    const text = "GRYFFINDOR";
    [...text].forEach((ch, i) => {
      const s = document.createElement("span");
      s.textContent = ch;
      s.style.animationDelay = (i * 0.1) + "s";
      house.appendChild(s);
    });
    scene.appendChild(house);
    Audio2.play("chime");
    await wait(5000);
  }

  async function questHub(state) {
    clear();
    const scene = el("div", "scene");
    const title = el("div", "name-reveal", "");
    const txt = "THE TRIALS";
    [...txt].forEach((ch, i) => {
      const s = document.createElement("span");
      s.innerHTML = ch === " " ? "&nbsp;" : ch;
      s.style.animationDelay = (i * 0.08) + "s";
      title.appendChild(s);
    });
    title.style.fontSize = "clamp(1.8rem, 7vw, 3.5rem)";
    scene.appendChild(title);

    const grid = el("div", "level-grid");
    for (let lvl = 1; lvl <= 4; lvl++) {
      const unlocked = state.quest.unlockedLevels.includes(lvl);
      const done = state.quest.answers[String(lvl)];
      const card = el("div", "level-card " + (unlocked ? "unlocked" : "locked"));
      card.innerHTML = '<span class="num">' + ["I","II","III","IV"][lvl-1] + '</span>' + (done ? "✓ Complete" : (unlocked ? "Begin" : "🔒 Locked"));
      if (unlocked && !done) {
        card.addEventListener("click", () => {
          if (window.__levelResolve) window.__levelResolve(lvl);
        });
      }
      grid.appendChild(card);
    }
    scene.appendChild(grid);
    stage().appendChild(scene);

    return new Promise((resolve) => { window.__levelResolve = resolve; });
  }

  async function levelScene(level) {
    clear();
    const scene = el("div", "scene");
    const prompt = Quest.LEVEL_PROMPTS[level];
    const cap = el("div", "caption");
    cap.innerHTML = "<strong>Level " + ["I","II","III","IV"][level-1] + "</strong><br><br>" + prompt.q;
    scene.appendChild(cap);

    const input = el("input", "answer-input");
    input.placeholder = prompt.placeholder;
    input.autocomplete = "off";
    scene.appendChild(input);

    const btn = el("button", "magic-btn", "Cast");
    scene.appendChild(btn);

    const feedback = el("div", "caption");
    feedback.style.marginTop = "1rem";
    feedback.style.minHeight = "2em";
    scene.appendChild(feedback);

    stage().appendChild(scene);
    input.focus();

    return new Promise((resolve) => {
      const submit = async () => {
        const val = input.value.trim();
        if (!val) return;
        feedback.innerHTML = "<em>The magic listens...</em>";
        try {
          const res = await API.answer(Session.id(), level, val);
          feedback.innerHTML = "<strong>✦ " + res.word.toUpperCase() + " ✦</strong>";
          Audio2.play("chime");
          await wait(2800);
          resolve(res);
        } catch (e) {
          if (e.code === "WRONG_ANSWER") {
            feedback.innerHTML = '<em style="color:#c97b6f;">The spell resists... try again.</em>';
            Audio2.play("wrong");
            Transitions.shake(scene);
            input.value = "";
          } else if (e.code === "ALREADY_ANSWERED") {
            resolve({ already: true });
          } else {
            feedback.innerHTML = '<em style="color:#c97b6f;">' + e.message + '</em>';
          }
        }
      };
      btn.addEventListener("click", submit);
      input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
    });
  }

  async function finaleReveal() {
    clear();
    const scene = el("div", "scene");

    const lines = [
      "Some people enter your life...",
      "Some stay for a while...",
      "And somehow, without even realizing it...",
    ];
    const cap = el("div", "finale-line");
    scene.appendChild(cap);
    stage().appendChild(scene);

    for (const line of lines) {
      cap.innerHTML = "";
      await typeText(cap, line, 55);
      await wait(2800);
    }

    cap.innerHTML = "";
    await wait(1200);
    const big = el("div", "name-reveal", "");
    big.style.fontSize = "clamp(1.5rem, 6.5vw, 3rem)";
    const words = ["You", "somehow", "became", "home."];
    for (const w of words) {
      const s = document.createElement("span");
      s.innerHTML = w + "&nbsp;";
      s.style.animationDelay = "0s";
      s.style.marginRight = "0.4em";
      big.appendChild(s);
      Audio2.play("sparkle");
      await wait(900);
    }
    scene.appendChild(big);
    await wait(5000);
  }

  async function chestScene() {
    clear();
    const scene = el("div", "scene");
    scene.style.background = "radial-gradient(ellipse at center, rgba(60,40,20,0.55), #000 70%)";
    const chest = el("div", "", '<div style="font-size:8rem;filter:drop-shadow(0 0 50px rgba(212,175,55,0.8));">🎁</div>');
    scene.appendChild(chest);
    const cap = el("div", "caption", "There is one final thing waiting for you.");
    cap.style.marginTop = "2rem";
    scene.appendChild(cap);

    const btn = el("button", "magic-btn", "🎁 Open Your Gift");
    scene.appendChild(btn);
    stage().appendChild(scene);

    return new Promise((resolve) => {
      btn.addEventListener("click", async () => {
        Audio2.play("boom");
        await Transitions.flashWhite(2200);
        resolve(true);
      });
    });
  }

  async function finalVideo(url) {
    clear();
    const scene = el("div", "scene");
    const v = el("video", "quest-video");
    v.src = url;
    v.controls = false;
    v.autoplay = true;
    v.playsInline = true;
    scene.appendChild(v);
    stage().appendChild(scene);
    try { await API.setFlag(Session.id(), "finalVideoCompleted", true); } catch(e){}

    return new Promise((resolve) => {
      v.addEventListener("ended", () => resolve(true));
      v.addEventListener("error", () => resolve(true));
    });
  }

  async function finalCakeButton() {
    clear();
    const scene = el("div", "scene");
    const cap = el("div", "caption", "One last thing...");
    scene.appendChild(cap);
    const cake = el("div", "cake-visual glow-pulse", "🎂");
    cake.style.marginTop = "2rem";
    cake.style.cursor = "pointer";
    scene.appendChild(cake);
    const hint = el("div", "caption", "<em>tap the cake when you're ready</em>");
    hint.style.marginTop = "2rem";
    hint.style.fontSize = "0.9em";
    hint.style.opacity = "0.6";
    scene.appendChild(hint);
    stage().appendChild(scene);

    return new Promise((resolve) => {
      cake.addEventListener("click", async () => {
        Audio2.play("boom");
        await Transitions.flashWhite(1200);
        resolve(true);
      }, { once: true });
    });
  }

  async function endScreen() {
    clear();
    const scene = el("div", "scene");
    const title = el("div", "name-reveal", "");
    const txt = "THE END";
    [...txt].forEach((ch, i) => {
      const s = document.createElement("span");
      s.innerHTML = ch === " " ? "&nbsp;" : ch;
      s.style.animationDelay = (i * 0.15) + "s";
      title.appendChild(s);
    });
    scene.appendChild(title);

    const sub = el("div", "caption", "<em>Thank you for taking the journey.</em>");
    sub.style.marginTop = "3rem";
    sub.style.opacity = 0;
    scene.appendChild(sub);
    stage().appendChild(scene);
    await wait(2000);
    sub.style.transition = "opacity 3s ease";
    sub.style.opacity = 1;
  }

  return {
    intro, gate, enterGate, spellPrompt, welcome,
    birthdayVisitor, cakeScene, confettiTransition,
    wallScene, alleyScene, ticketScene, trainScene, castleScene,
    hatScene, questHub, levelScene, finaleReveal,
    chestScene, finalVideo, finalCakeButton, endScreen,
    clear, wait, typeText, el,
  };
})();
