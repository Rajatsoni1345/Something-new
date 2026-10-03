const Session = (() => {
  const KEY = "tanisha_quest_session_id";
  let current = null;

  async function bootstrap() {
    let sid = localStorage.getItem(KEY);
    if (sid) {
      try {
        current = await API.resumeSession(sid);
        return current;
      } catch (e) {
        localStorage.removeItem(KEY);
      }
    }
    current = await API.createSession();
    localStorage.setItem(KEY, current.sessionId);
    return current;
  }

  function get() { return current; }
  function id() { return current && current.sessionId; }

  async function refresh() {
    if (!current) return null;
    current = await API.getSession(current.sessionId);
    return current;
  }

  return { bootstrap, get, id, refresh };
})();
