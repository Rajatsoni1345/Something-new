# Birthday Quest — State Machine

## Overview

Every quest is a linear, forward-only state machine. The
client can never skip a step. Every transition is validated
on the server and committed atomically to Firestore.

## Transition rules

1. Every transition is checked by `can_transition()`.
2. Illegal transitions raise `ValueError`.
3. Only `transition_quest()` may set `SESSION_COMPLETE`.
4. `SESSION_COMPLETE` is terminal. It sets `active=False`.
5. Every transition runs inside a Firestore transaction.
6. Optimistic version checks prevent stale writes.
7. The client never chooses the next state directly.

## Special states

### VIDEO_1_RECORDING

- Camera only. No microphone.
- Candle blow detection triggers the next step.
- Fallback: `I blew it` button.

### CANDLE_TRIGGERED

- Video 1 recording is stopped.
- Blob is uploaded to Cloudinary.
- Verified before any progress.

### VIDEO_1_VERIFIED

- Server confirms the video exists in Cloudinary.
- Only then does `VIDEO_2_READY` open.

### VIDEO_2_RECORDING

- Fresh MediaRecorder instance.
- Camera + microphone.
- Previous instance is never reused.

### REACTION_RECORDING

- Final reaction capture.
- Triggered by the cake button.
- Stopped and uploaded immediately.

### SESSION_COMPLETE

- Session becomes inactive.
- `completed_at` is written.
- No further transitions are allowed.

## Recovery

If the frontend is refreshed, reloaded, or the browser is
closed and reopened:

The backend returns the current session state. The frontend
must resume from that exact state — never restart from
`NEW`.

## Anti-bypass guarantees

- A session cannot jump to a later state.
- Hidden words cannot be claimed out of order.
- Level answers are validated server-side.
- Recording uploads are verified before any state advances.
- A completed session cannot be reopened.
## States (in strict order)

