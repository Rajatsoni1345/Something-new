const API = (() => {
  const BASE = "";

  async function call(path, opts = {}) {
    const res = await fetch(BASE + path, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok || !json.success) {
      const err = json.error || { code: "NETWORK", message: "Magic connection flickered." };
      throw Object.assign(new Error(err.message), { code: err.code });
    }
    return json.data;
  }

  return {
    health: () => call("/api/v1/health"),
    createSession: () => call("/api/v1/session/create", { method: "POST" }),
    getSession: (sid) => call(`/api/v1/session/${sid}`),
    resumeSession: (sid) => call(`/api/v1/session/${sid}/resume`, { method: "POST" }),

    answer: (sid, level, answer) =>
      call(`/api/v1/quest/${sid}/answer`, {
        method: "POST",
        body: JSON.stringify({ level, answer }),
      }),
    collect: (sid, item) =>
      call(`/api/v1/quest/${sid}/collect`, {
        method: "POST",
        body: JSON.stringify({ item }),
      }),
    setFlag: (sid, flag, value = true) =>
      call(`/api/v1/quest/${sid}/flag`, {
        method: "POST",
        body: JSON.stringify({ flag, value }),
      }),
    setScene: (sid, scene) =>
      call(`/api/v1/quest/${sid}/scene`, {
        method: "POST",
        body: JSON.stringify({ scene }),
      }),

    startRecording: (sid, type) =>
      call(`/api/v1/recordings/start`, {
        method: "POST",
        body: JSON.stringify({ session_id: sid, type }),
      }),
    stopRecording: (sid, type) =>
      call(`/api/v1/recordings/stop`, {
        method: "POST",
        body: JSON.stringify({ session_id: sid, type }),
      }),
    uploadRecording: (sid, type, blob, onProgress) => {
      return new Promise((resolve, reject) => {
        const form = new FormData();
        form.append("session_id", sid);
        form.append("type", type);
        form.append("video", blob, `${type}.webm`);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/v1/recordings/upload");
        xhr.upload.onprogress = (e) => {
          if (onProgress && e.lengthComputable) onProgress(e.loaded / e.total);
        };
        xhr.onload = () => {
          try {
            const j = JSON.parse(xhr.responseText);
            if (j.success) resolve(j.data);
            else reject(Object.assign(new Error(j.error && j.error.message), { code: j.error && j.error.code }));
          } catch (err) { reject(err); }
        };
        xhr.onerror = () => reject(new Error("Upload failed"));
        xhr.send(form);
      });
    },
  };
})();
