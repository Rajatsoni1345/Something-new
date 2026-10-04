# Deploy — Render + GitHub Actions

This document describes how to deploy the Birthday Quest
backend to Render and how continuous integration works on
GitHub Actions.

## 1. Firebase service account

1. Open Firebase Console → Project Settings →
   Service Accounts.
2. Click **Generate new private key**.
3. Download the JSON file.
4. Copy these values — they will go into Render env vars:
   - `project_id`
   - `private_key_id`
   - `private_key`
   - `client_email`
   - `client_id`

Never commit the JSON file to Git.

## 2. Cloudinary

1. Open https://console.cloudinary.com/settings/api-keys
2. Copy:
   - Cloud name
   - API key
   - API secret

## 3. Render

1. Push the repository to GitHub.
2. On Render, create a new **Web Service**.
3. Connect the GitHub repository.
4. Render automatically detects `backend/render.yaml`.
5. In the Render dashboard, set every env var marked
   `sync: false` in `render.yaml`:

   - `SECRET_KEY`
   - `FRONTEND_ORIGIN`
   - `TRUSTED_HOSTS`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_PRIVATE_KEY_ID`
   - `FIREBASE_PRIVATE_KEY`
   - `FIREBASE_CLIENT_EMAIL`
   - `FIREBASE_CLIENT_ID`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `ADMIN_UIDS`
   - `ADMIN_EMAILS`

6. Deploy.

Expected response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "Birthday Quest",
    "environment": "production"
  }
}
