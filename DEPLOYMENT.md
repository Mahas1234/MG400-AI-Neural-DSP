# 🌐 MG400 AI: Deployment Guide

This guide covers how to deploy the **Web Remote (Next.js)** to the cloud and bundle the **Desktop Bridge (Python)** for end-users.

---

## 1. Web Remote Development & Deployment (Vercel)

The web folder contains a Next.js 16 application that acts as the global control surface.

### A. Environment Variables
You must set these in your hosting provider (Vercel, Railway, etc.):

| Key | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Your Google AI Studio key for tone generation. |
| `PUSHER_APP_ID` | From your Pusher Dashboard. |
| `NEXT_PUBLIC_PUSHER_KEY` | Public key for the client-side sync. |
| `PUSHER_SECRET` | Secret key for server-side triggers. |
| `NEXT_PUBLIC_PUSHER_CLUSTER` | e.g., `ap2`. |

### B. Deploy to Vercel (Recommended)
1. Push your code to GitHub.
2. Import the repository into [Vercel](https://vercel.com).
3. Set the **Root Directory** to `web`.
4. Add the Environment Variables listed above.
5. Click **Deploy**.

---

## 2. Desktop Bridge Distribution (macOS)

The desktop app handles the physical USB MIDI connection to the MG-400.

### A. Local Requirements
Users will need:
- Python 3.9+ (if running from source).
- NUX MG-400 connected via USB.

### B. Creating a Standalone Bundle (.dmg)
We use **PyInstaller** to create a single executable that users can drag into their Applications folder.

1. **Install Build Tools:**
   ```bash
   pip install pyinstaller dmgbuild
   ```
2. **Execute Build Script:**
   ```bash
   ./build_mac.sh
   ```
3. Your production-ready `.dmg` will be located in the `dist/` folder.

---

## 3. The "Neural Cloud Mesh" Workflow

Once deployed, the ecosystem works like this:

1.  **Desktop Bridge** is opened on the user's Mac. It detects the MG-400 and connects to the **Pusher** global channel.
2.  **Web Remote** is opened on the user's Phone/Tablet (via your Vercel URL).
3.  When the user adjusts a parameter on their phone:
    - Phone sends data to `https://your-app.vercel.app/api/stream`.
    - Vercel triggers a Pusher event.
    - Pusher broadcasts to the **Desktop Bridge**.
    - Desktop Bridge sends the `MIDI CC` command to the hardware.
4.  **Success:** The hardware updates in real-time, anywhere in the world.

---

## 4. Troubleshooting
- **No Sync:** Check that the `PUSHER_SECRET` matches across the Web and Desktop app.
- **AI Fault:** Ensure the `GEMINI_API_KEY` has balance/quota and supports `gemini-2.5-flash`.
- **MIDI Error:** Ensure no other MIDI application (like NUX QuickTone) is holding the hardware port.
