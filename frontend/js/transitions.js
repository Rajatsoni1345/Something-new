const Transitions = (() => {
  function flashWhite(duration) {
    duration = duration || 2500;
    return new Promise((resolve) => {
      const el = document.createElement("div");
      el.className = "transition-white";
      document.body.appendChild(el);
      setTimeout(() => { el.remove(); resolve(); }, duration);
    });
  }

  function flashBlack(duration) {
    duration = duration || 3500;
    return new Promise((resolve) => {
      const el = document.createElement("div");
      el.className = "transition-black";
      document.body.appendChild(el);
      setTimeout(() => { el.remove(); resolve(); }, duration);
    });
  }

  function cameraForward(el, duration) {
    duration = duration || 5000;
    return new Promise((resolve) => {
      if (el) el.classList.add("camera-forward");
      setTimeout(resolve, duration);
    });
  }

  function cameraBack(el, duration) {
    duration = duration || 5000;
    return new Promise((resolve) => {
      if (el) el.classList.add("camera-back");
      setTimeout(resolve, duration);
    });
  }

  function rackFocus(el, duration) {
    duration = duration || 4000;
    return new Promise((resolve) => {
      if (el) el.classList.add("rack-focus");
      setTimeout(resolve, duration);
    });
  }

  function confetti(count, duration) {
    count = count || 180;
    duration = duration || 9000;
    const colors = ["#c9a961", "#e8c87a", "#7ecbff", "#ff9d3d", "#d8cfb8", "#8b2f2f"];
    for (let i = 0; i < count; i++) {
      const p = document.createElement("div");
      p.className = "confetti-piece";
      p.style.left = Math.random() * 100 + "vw";
      p.style.background = colors[Math.floor(Math.random() * colors.length)];
      p.style.animationDuration = (4 + Math.random() * 4) + "s";
      p.style.animationDelay = (Math.random() * 2) + "s";
      p.style.opacity = 0.4 + Math.random() * 0.6;
      document.body.appendChild(p);
      setTimeout(() => p.remove(), duration + 6000);
    }
  }

  function shake(el) {
    if (!el) return;
    el.classList.add("shake");
    setTimeout(() => el.classList.remove("shake"), 900);
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

  return { flashWhite, flashBlack, cameraForward, cameraBack, rackFocus, confetti, shake, recIndicator };
})();
