# ☽ Empire & Ink — AI Mughal Art Studio

> Transform any idea into a stunning Mughal miniature painting using Google Gemini AI.

**Empire & Ink** is a full-stack Python web application that lets users generate and transform images into the style of historical Mughal miniature paintings. Built as a single deployable service with FastAPI + Jinja2 templates, backed by Supabase and powered by Google Gemini.

---

## Features

| Feature | Description |
|---|---|
| **Generate Art** | Type any prompt → AI produces a Mughal miniature painting (Imagen 4 + Gemini Flash fallback) |
| **Transform Photo** | Upload any photo → AI converts it to Mughal style (Gemini Flash multimodal) |
| **3 Art Presets** | Akbari · Jahangiri · Shahjahani — each with era-specific style descriptors |
| **Smart Prompt Enhancement** | Gemini Flash rewrites your raw idea into a rich Mughal art prompt |
| **Personal Gallery** | All artworks saved to Supabase Storage, viewable in a fullscreen lightbox |
| **Re-transform** | Apply a different style to any existing artwork from the gallery |
| **Auth** | Secure email/password login via Supabase Auth |
| **Mughal UI** | Ornate jewel-tone dark theme with Playfair Display typography |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Frontend | Jinja2 HTML Templates + Tailwind CSS + Vanilla JavaScript |
| AI Image Generation | Google Imagen 4 (`imagen-4.0-generate-001`) → Gemini Flash fallback |
| AI Prompt Enhancement | Gemini 2.5 Flash text model |
| AI Image Transformation | Gemini 2.5 Flash multimodal (image → Mughal painting) |
| Database | Supabase PostgreSQL |
| File Storage | Supabase Storage |
| Authentication | Supabase Auth (JWT + RLS) |
| Deployment | Render free tier |

---

## Folder Structure

```
empire-ink/
├── main.py                      # App entrypoint — FastAPI app + Jinja2 page routes
├── requirements.txt             # All Python dependencies
├── .env.example                 # Environment variable template
├── .env                         # Your local secrets (never commit this)
├── render.yaml                  # Render deployment configuration
├── CLAUDE.md                    # AI assistant context file
├── README.md                    # This file
│
├── app/
│   ├── config.py                # Pydantic Settings — reads .env variables
│   ├── database.py              # Supabase client factory (anon / service role)
│   │
│   ├── ai/
│   │   ├── prompt_enhancer.py   # Gemini Flash text: rewrites prompt into rich Mughal art prompt
│   │   ├── image_generator.py   # Imagen 4 primary + Gemini Flash fallback (text → image)
│   │   └── image_transformer.py # Gemini Flash multimodal: photo + style → Mughal painting
│   │
│   ├── services/
│   │   ├── auth_service.py      # sign_up, sign_in, sign_out via Supabase Auth
│   │   ├── gallery_service.py   # DB CRUD + Supabase Storage upload/delete/fetch
│   │   └── generation_service.py# Orchestrates full AI pipeline (generate + transform)
│   │
│   └── api/
│       ├── schemas.py           # Pydantic request/response models
│       └── routes.py            # All FastAPI API routes
│
├── templates/
│   ├── base.html                # Shared layout: Tailwind config, navbar, font imports
│   ├── login.html               # /login page
│   ├── register.html            # /register page
│   ├── home.html                # / studio page: Generate + Transform tabs
│   └── gallery.html             # /gallery: artwork grid, lightbox, re-transform, download
│
└── static/
    ├── app.js                   # Auth helpers, apiFetch wrapper, downloadImage
    └── mughal.css               # Supplemental Mughal theme styles
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Register new account |
| `POST` | `/api/auth/login` | — | Sign in, returns JWT |
| `POST` | `/api/auth/logout` | ✓ | Invalidate session |
| `POST` | `/api/generate` | ✓ | Text prompt + style → Mughal art image URL |
| `POST` | `/api/transform` | ✓ | Upload photo + style → Mughal-styled image URL |
| `GET` | `/api/gallery` | ✓ | Fetch all artworks for the logged-in user |
| `DELETE` | `/api/gallery/{id}` | ✓ | Delete an artwork (DB record + Storage file) |
| `GET` | `/api/docs` | — | Swagger UI |

All protected endpoints require `Authorization: Bearer <token>` (Supabase JWT).

---

## Local Setup

### 1. Prerequisites
- Python 3.11 or higher
- A [Supabase](https://supabase.com) account (free)
- A [Google AI Studio](https://aistudio.google.com) API key (Gemini)

### 2. Clone and install

```bash
git clone https://github.com/your-username/empire-ink.git
cd empire-ink

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Set up Supabase

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Open **SQL Editor** and run:

```sql
-- Create galleries table
CREATE TABLE galleries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    enhanced_prompt TEXT,
    image_url TEXT NOT NULL,
    style_preset VARCHAR(50) DEFAULT 'akbari',
    model_used VARCHAR(50),
    source_type VARCHAR(20) DEFAULT 'generate',
    parent_id UUID REFERENCES galleries(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE galleries ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "select_own" ON galleries FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "insert_own" ON galleries FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "delete_own" ON galleries FOR DELETE USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX galleries_user_id_idx ON galleries(user_id);
CREATE INDEX galleries_created_at_idx ON galleries(created_at DESC);
```

3. Go to **Storage** → **New Bucket** → Name: `empire-ink-gallery` → **Public bucket** ✓
4. Go to **Project Settings → API** → copy your **Project URL**, **anon key**, and **service_role key**

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_BUCKET=empire-ink-gallery
```

### 5. Run locally

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.
API docs at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

---

## Deploy to Render

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit — Empire & Ink"
git branch -M main
git remote add origin https://github.com/your-username/empire-ink.git
git push -u origin main
```

> Add `.env` to `.gitignore` — never commit secrets!

### 2. Create a Render Web Service

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repository
3. Render auto-detects `render.yaml` and configures the service

**Manual settings (if not using render.yaml):**

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

### 3. Set environment variables in Render

In **Environment** tab add:

```
GEMINI_API_KEY        = your_key
SUPABASE_URL          = https://your-project.supabase.co
SUPABASE_ANON_KEY     = your_anon_key
SUPABASE_SERVICE_KEY  = your_service_key
SUPABASE_BUCKET       = empire-ink-gallery
APP_ENV               = production
```

### 4. Deploy

Click **Deploy**. Your live URL: `https://empire-ink.onrender.com`

> **Render free tier:** The service sleeps after 15 minutes of inactivity and cold-starts in ~30 seconds.

---

## Supabase Auth Configuration

By default Supabase requires email confirmation. To disable for development:

1. Supabase Dashboard → **Authentication** → **Settings**
2. Under **Email Auth** → disable **"Enable email confirmations"**

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✓ | Google AI Studio API key |
| `SUPABASE_URL` | ✓ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✓ | Supabase anon/public key (used for auth validation) |
| `SUPABASE_SERVICE_KEY` | ✓ | Supabase service role key (server-side only, never expose) |
| `SUPABASE_BUCKET` | ✓ | Storage bucket name (default: `empire-ink-gallery`) |
| `APP_ENV` | — | `development` or `production` (default: `development`) |
| `APP_HOST` | — | Host to bind (default: `0.0.0.0`) |
| `APP_PORT` | — | Port to run on locally (default: `8000`) |

---

## Mughal Style Presets

| Preset | Era | Visual Character |
|---|---|---|
| `akbari` | 1556–1605 | Bold outlines, Persian-Indian fusion, deep jewel tones, busy multi-figure compositions |
| `jahangiri` | 1605–1627 | Naturalistic fine detail, pastel palette, gold leaf borders, botanical accuracy |
| `shahjahani` | 1628–1658 | White marble aesthetic, refined symmetry, ivory + gold, opulent floral borders |

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com) — Python API framework
- [Jinja2](https://jinja.palletsprojects.com) — HTML templating
- [Tailwind CSS](https://tailwindcss.com) — Utility-first CSS framework
- [Google Gemini API](https://ai.google.dev) — AI image generation and prompt enhancement
- [Supabase](https://supabase.com) — Database, auth, and file storage
- [Render](https://render.com) — Cloud deployment

---

*Empire & Ink — Where History Meets the Future*
