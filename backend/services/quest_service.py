import logging
from .session_service import get_session, update_session

logger = logging.getLogger(__name__)

LEVELS = {
    1: {"answer": "lumos",     "word": "you"},
    2: {"answer": "alohomora", "word": "somehow"},
    3: {"answer": "expecto",   "word": "became"},
    4: {"answer": "patronum",  "word": "home"},
}

def submit_answer(session_id, level, answer):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    
    unlocked = s["quest"]["unlockedLevels"]
    if level not in unlocked:
        return {"error": "LEVEL_LOCKED"}
    
    if str(level) in s["quest"]["answers"]:
        return {"error": "ALREADY_ANSWERED", "state": s}
    
    correct = LEVELS.get(level, {}).get("answer", "").strip().lower()
    if answer.strip().lower() != correct:
        return {"error": "WRONG_ANSWER"}
    
    collected_words = s["quest"]["collectedWords"] + [LEVELS[level]["word"]]
    unlocked_levels = s["quest"]["unlockedLevels"][:]
    if level < 4 and (level + 1) not in unlocked_levels:
        unlocked_levels.append(level + 1)
    
    answers = s["quest"]["answers"]
    answers[str(level)] = answer.strip().lower()
    
    updates = {
        "quest.level": level,
        "quest.answers": answers,
        "quest.collectedWords": collected_words,
        "quest.unlockedLevels": unlocked_levels,
        "currentLevel": level,
    }
    update_session(session_id, updates)
    logger.info(f"LEVEL_UNLOCKED session={session_id} level={level}")
    return {"state": get_session(session_id), "word": LEVELS[level]["word"]}

def collect_item(session_id, item):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    if item not in ["owl", "wand", "broom"]:
        return {"error": "INVALID_ITEM"}
    
    collectibles = s["quest"]["collectibles"]
    collectibles[item] = True
    
    all_collected = all(collectibles.values())
    updates = {"quest.collectibles": collectibles}
    if all_collected:
        updates["currentScene"] = "TICKET"
    update_session(session_id, updates)
    logger.info(f"COLLECTED session={session_id} item={item}")
    return {"state": get_session(session_id), "allCollected": all_collected}

def set_flag(session_id, flag, value=True):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    flags = s.get("flags", {})
    flags[flag] = value
    update_session(session_id, {"flags": flags})
    return {"state": get_session(session_id)}

def set_scene(session_id, scene):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    update_session(session_id, {"currentScene": scene})
    logger.info(f"SCENE_STARTED session={session_id} scene={scene}")
    return {"state": get_session(session_id)}
