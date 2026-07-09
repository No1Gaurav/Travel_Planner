# 🌍 Voyager AI — IBM Watsonx.ai Travel Planner Agent

> An AI-powered travel planning web application built with **Python Flask** and **IBM Watsonx.ai (Granite-3.3-8B Instruct)**. Featuring a full-featured chat UI, smart itinerary generator, budget dashboard, traveler profile management, and destination recommendations.

---

## 📁 Project Structure

```
travel-planner-agent/
├── app.py                  # Flask backend + IBM Watsonx.ai integration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .env                    # Your secrets (never commit this!)
└── templates/
    └── index.html          # Full frontend (Bootstrap + dark mode + chat UI)
```

---

## ✨ Features

| Feature | Description |
|---|---|
| **AI Chat Planner** | Conversational interface powered by IBM Granite LLM |
| **Smart Itinerary Planner** | Day-by-day travel plans with hotels, cafés & costs |
| **Budget Dashboard** | Visual cost breakdown with animated bars & savings tips |
| **Destination Recommendations** | Hidden gems tailored to your profile |
| **Traveler Profile** | Family/group support with member management |
| **Dark Mode** | Toggle between light/dark themes (persisted in localStorage) |
| **Mobile Responsive** | Full Bootstrap 5 responsive layout with sidebar drawer |
| **`AGENT_INSTRUCTIONS`** | Central config block to customise AI tone, budget tiers & preferences |

---

## 🔧 Prerequisites

- Python 3.9+
- An **IBM Cloud account** with Watsonx.ai enabled
- An **IBM Cloud API Key**
- A **Watsonx.ai Project ID**

---

## 🚀 Quick Start

### 1. Clone / Copy the project

```bash
cd travel-planner-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your IBM credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_watsonx_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=any-random-secret-string
FLASK_DEBUG=False
PORT=5000
```

> **How to get credentials:**
> 1. Log in to [cloud.ibm.com](https://cloud.ibm.com)
> 2. Go to **Manage → Access (IAM) → API Keys** → Create an API key
> 3. Open [Watsonx.ai](https://dataplatform.cloud.ibm.com) → Create/open a project → copy the **Project ID** from the project settings

### 5. Run the application

```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🤖 Customising Agent Behavior (`AGENT_INSTRUCTIONS`)

Open [`app.py`](app.py) and find the `AGENT_INSTRUCTIONS` dictionary near the top of the file. This is your single control panel for the AI agent:

```python
AGENT_INSTRUCTIONS = {
    # Change the agent's name, tone, and personality
    "persona": "You are an expert AI Travel Planner named 'Voyager AI'...",

    # Add or adjust budget tiers (hotel ranges, food costs, transport)
    "budget_tiers": {
        "budget":   {"label": "Budget",   "hotel_range": "$20–$60/night", ...},
        "moderate": {"label": "Moderate", "hotel_range": "$60–$150/night", ...},
        "luxury":   {"label": "Luxury",   "hotel_range": "$150+/night", ...},
    },

    # Define what output the AI must always include
    "output_rules": "Always structure itineraries day-by-day...",

    # Adjust safety guidelines
    "safety_note": "Never recommend unsafe or illegal activities...",
}
```

**Common customisations:**

| Goal | What to change |
|---|---|
| Change agent name/tone | `persona` field |
| Change budget ranges | `budget_tiers[tier]["hotel_range"]` etc. |
| Change default trip style | `default_trip_style` |
| Add a new budget tier (e.g. "ultra-luxury") | Add entry to `budget_tiers` |
| Force specific output format | Edit `output_rules` |
| Add a new language | Append to `supported_languages` |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main web application |
| `POST` | `/api/chat` | Conversational AI chat |
| `POST` | `/api/itinerary` | Generate day-by-day itinerary |
| `POST` | `/api/budget` | Budget breakdown analysis |
| `POST` | `/api/recommendations` | Destination recommendations |
| `GET` | `/api/health` | Agent health check |

### Example — Chat request

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Plan a 5-day trip to Kyoto for 2 adults on a moderate budget",
    "profile": {
      "group_type": "couple",
      "travelers": 2,
      "children": 0,
      "budget": "moderate",
      "trip_style": "cultural"
    },
    "history": []
  }'
```

### Example — Budget request

```bash
curl -X POST http://localhost:5000/api/budget \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Bali, Indonesia",
    "days": 7,
    "profile": { "travelers": 2, "children": 0, "budget": "moderate" }
  }'
```

---

## ☁️ Deployment

### Option A — Gunicorn (Linux / macOS production)

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### Option B — IBM Code Engine

1. Install IBM Cloud CLI:  
   `curl -fsSL https://clis.cloud.ibm.com/install/linux | sh`

2. Login and target a region:
   ```bash
   ibmcloud login --apikey $IBM_API_KEY -r us-south
   ibmcloud ce project create --name voyager-ai
   ibmcloud ce project select --name voyager-ai
   ```

3. Create a secret from your `.env`:
   ```bash
   ibmcloud ce secret create --name voyager-env \
     --from-env-file .env
   ```

4. Deploy the application:
   ```bash
   ibmcloud ce application create \
     --name voyager-ai \
     --image icr.io/your-namespace/voyager-ai:latest \
     --env-from-secret voyager-env \
     --port 5000 \
     --min-scale 0 --max-scale 3
   ```

### Option C — Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t voyager-ai .
docker run -p 5000:5000 --env-file .env voyager-ai
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it is listed in `.gitignore` by default.
- Use `.env.example` as the template for collaborators.
- Rotate your IBM Cloud API Key regularly.
- In production, set `FLASK_DEBUG=False` and use HTTPS behind a reverse proxy (nginx).

---

## 🧩 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + Flask 3.0 |
| AI Model | IBM Watsonx.ai — `ibm/granite-3-3-8b-instruct` |
| SDK | `ibm-watsonx-ai` Python SDK |
| Frontend | Bootstrap 5.3 + Bootstrap Icons + vanilla JS |
| Fonts | Google Fonts — Inter |
| Config | python-dotenv |
| Production server | Gunicorn |

---

## 🗺️ Roadmap Ideas

- [ ] Multi-language UI (i18n)
- [ ] PDF/Word itinerary export
- [ ] Live hotel price integration (Booking.com API)
- [ ] Map view with Leaflet.js
- [ ] User authentication (Flask-Login)
- [ ] Save/load trip history

---

*Made with ❤️ using IBM Watsonx.ai and Granite models.*




🌍 Voyager AI — Complete Project Delivered
📁 Files created in travel-planner-agent/
File	Lines	Purpose
app.py	270	Flask backend + IBM Watsonx.ai + AGENT_INSTRUCTIONS
templates/index.html	1,238	Full SPA frontend
requirements.txt	6	Python dependencies
.env.example	13	Credential template
README.md	279	Full deployment guide
🤖 AGENT_INSTRUCTIONS — your single control panel (top of app.py)
AGENT_INSTRUCTIONS = {
    "persona":          "...",   # ← Change agent name / tone / personality
    "budget_tiers":     {...},   # ← Adjust hotel ranges, food costs per tier
    "default_budget":   "moderate",
    "output_rules":     "...",   # ← Control what AI always includes
    "supported_languages": [...],
    "safety_note":      "...",
}

🚀 To run in 3 commands
# 1. Install deps
pip install -r requirements.txt

# 2. Copy .env.example → .env, fill in IBM_API_KEY + IBM_PROJECT_ID

# 3. Run
python app.py
# → http://localhost:5000

🎛️ Frontend sections
Dashboard — hero banner, stat cards, quick-plan form
AI Chat Planner — streaming-style chat with quick-action chips & typing animation
Smart Itinerary — slider for days, style/budget selectors, copy-to-clipboard output
Budget Dashboard — animated progress bars with category breakdown + AI savings tips
Recommendations — free-text query + AI hidden-gem suggestions
Traveler Profile — name, group type, family/group member list, persisted in localStorage
