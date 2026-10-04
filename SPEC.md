# Birthday Quest — Master Specification

## Overview

Birthday Quest is a cinematic, mysterious, full-screen web
experience built for one specific person. The journey moves
through magical scenes inspired by classic fantasy imagery,
ending with a personal birthday video and captured reaction.

## Layers

| Layer    | Tech                        |
|----------|-----------------------------|
| Frontend | HTML, CSS, JavaScript       |
| Backend  | Flask (Python 3.12)         |
| State    | Firebase Firestore          |
| Storage  | Cloudinary (video files)    |
| Hosting  | Render                      |
| CI       | GitHub Actions              |

## Recording engine

The recording engine is the core non-negotiable behaviour.

Video 1 and Video 2 never share a MediaRecorder instance.
This is a hard rule.

## Scene to API mapping

| Scene               | Endpoint                               |
|---------------------|----------------------------------------|
| Health check        | GET  /api/v1/health                    |
| Create session      | POST /api/v1/sessions                  |
| Recover session     | POST /api/v1/sessions/recover          |
| Read session        | GET  /api/v1/sessions/{id}             |
| Get quest state     | POST /api/v1/quest/state               |
| Complete level      | POST /api/v1/quest/levels/complete     |
| Collect item        | POST /api/v1/quest/items/collect       |
| Discover word       | POST /api/v1/quest/words/discover      |
| Unlock final reveal | POST /api/v1/quest/final-reveal/unlock |
| Start recording     | POST /api/v1/recordings/start          |
| Stop recording      | POST /api/v1/recordings/stop           |
| Mark upload pending | POST /api/v1/recordings/upload-pending |
| Upload video        | POST /api/v1/recordings/upload         |
| Verify video        | POST /api/v1/recordings/verify         |
| Mark failed         | POST /api/v1/recordings/fail           |
| Get recording       | GET  /api/v1/recordings/{id}           |
| Reaction start      | POST /api/v1/reactions/start           |
| Reaction stop       | POST /api/v1/reactions/stop            |
| Reaction upload     | POST /api/v1/reactions/upload          |
| Reaction verify     | POST /api/v1/reactions/verify          |
| Reaction status     | POST /api/v1/reactions/status          |
| Admin identity      | GET  /api/v1/admin/me                  |

## QR contract

The QR code must contain ONLY the permanent frontend URL.

The QR must never contain:

- a localhost address
- a temporary tunnel URL
- a Cloudinary URL
- a Firebase URL
- an IP address
- a session ID

The frontend decides on first visit whether to create a
session or recover an existing one.

## Security

- Firebase credentials only via environment variables.
- Cloudinary credentials only via environment variables.
- Session IDs are UUID v4, generated server-side.
- Admin access requires a Firebase ID token.
- All quest answers are validated server-side.
- All video uploads are verified in Cloudinary before
  the quest proceeds.
