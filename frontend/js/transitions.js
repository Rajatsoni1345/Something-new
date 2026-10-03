const Transitions = (() => {
  function flashWhite(duration) {
    duration = duration || 2000;
    return new Promise((resolve) => {
      const el = document.createElement("div");
      el.className = "fullscreen-transition transition-white";
      document.body.appendChild(el);
      setTimeout(() => { el.remove(); resolve(); }, duration);
    });
  }

  function flashBlack(duration) {
    duration = duration || 2500;
    return new Promise((resolve) => {
      const el = document.createElement("div");
      el.className = "fullscreen-transition transition-black";
      document.body.appendChild(el);
      setTimeout(() => { el.remove(); resolve(); }, duration);
    });
  }

  function cameraForward(el, duration) {
    duration = duration || 4000;
    return new Promise((resolve) => {
      if (el) el.classList.add("camera-forward");
      setTimeout(resolve, duration);
    });
  }

  function confetti(count, duration) {
    count = count || 120;
    duration = duration || 6000;
    const colors = ["#d4af37", "#f4d97b", "#7ecbff", "#ff9d3d", "#e8e0cf"];
    for (let i = 0; i < count; i++) {
      const p = document.createElement("div");
      p.className = "confetti-piece";
      p.style.left = Math.random() * 100 + "vw";
      p.style.background = colors[Math.floor(Math.random() * colors.length)];
      p.style.animationDuration = (3 + Math.random() * 3) + "s";
      p.style.animationDelay = (Math.random() * 1.5) + "s";
      p.style.transform = "rotate(" + (Math.random() * 360) + "deg)";
      document.body.appendChild(p);
      setTimeout(() => p.remove(), duration + 3000);
    }
  }

  function shake(el) {
    if (!el) return;
    el.classList.add("shake");
    setTimeout(() => el.classList.remove("shake"), 700);
  }

  function recIndicator(show) {
    let dot = document.getElementById("rec-dot");
    if (show) {
      if (!dot) {
        dot = document.createElement("div");
        dot.id = "rec-dot";
        dot.className = "rec-dot";
        document.body.appendChild(dot);
      }
    } else if (dot) {
      dot.remove();
    }
  }

  return { flashWhite, flashBlack, cameraForward, confetti, shake, recIndicator };
})();
