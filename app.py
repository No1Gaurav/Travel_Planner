

# =============================================================================
#  AI Travel Planner Agent — Flask Backend
#  Powered by IBM Watsonx.ai (Granite model)
# =============================================================================

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes

# ─────────────────────────────────────────────────────────────────────────────
# AGENT INSTRUCTIONS — Customise the agent's behavior, tone, and preferences
# ─────────────────────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {
    # General persona
    "persona": (
        "You are an expert AI Travel Planner named 'Voyager AI', powered by IBM Watsonx.ai. "
        "You are friendly, knowledgeable, culturally sensitive, and highly organised. "
        "You speak in a warm, professional tone and always personalise your advice."
    ),

    # Budget tiers and defaults
    "budget_tiers": {
        "budget":   {"label": "Budget",   "hotel_range": "$20–$60/night",  "daily_food": "$15–$30/day",  "transport": "public transit / shared rides"},
        "moderate": {"label": "Moderate", "hotel_range": "$60–$150/night", "daily_food": "$30–$80/day",  "transport": "mix of public & private"},
        "luxury":   {"label": "Luxury",   "hotel_range": "$150+/night",    "daily_food": "$80–$200/day", "transport": "private transfers & premium"},
    },
    "default_budget": "moderate",

    # Trip style preferences
    "trip_styles": ["adventure", "cultural", "relaxation", "family", "business", "romantic", "backpacking"],
    "default_trip_style": "cultural",

    # Traveler group defaults
    "group_types": ["solo", "couple", "family", "group of friends", "business group"],
    "default_group": "couple",

    # Output format rules
    "output_rules": (
        "Always structure itineraries day-by-day. "
        "Include: morning / afternoon / evening activities, recommended hotels, "
        "local cafés & restaurants, estimated costs per item, and travel tips. "
        "Highlight UNESCO sites, hidden gems, and safety notes where relevant. "
        "Return budget breakdowns as JSON when the endpoint requests it."
    ),

    # Languages the agent should respond in (follow user's language when detected)
    "supported_languages": ["English", "French", "Spanish", "Arabic", "German"],
    "default_language": "English",

    # Safety & content policy
    "safety_note": (
        "Never recommend unsafe or illegal activities. "
        "Advise travellers on local laws, visa requirements, and health precautions. "
        "Always suggest travel insurance."
    ),
}
# ─────────────────────────────────────────────────────────────────────────────


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "voyager-ai-secret-2024")
CORS(app)

# ── IBM Watsonx.ai client ─────────────────────────────────────────────────────
IBM_API_KEY    = os.getenv("IBM_API_KEY")
IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID")
IBM_URL        = os.getenv("IBM_WATSONX_URL", "https://au-syd.dai.cloud.ibm.com")

def get_watsonx_model() -> ModelInference:
    # CPD / on-prem URLs (anything that is NOT *.ml.cloud.ibm.com) require
    # `version` and `username` in Credentials.  IBM Cloud SaaS needs neither.
    is_cpd = "ml.cloud.ibm.com" not in IBM_URL
    if is_cpd:
        credentials = Credentials(
            url=IBM_URL,
            api_key=IBM_API_KEY,
            username=os.getenv("IBM_CPD_USERNAME"),
            version=os.getenv("IBM_CPD_VERSION", "5.1"),
        )
    else:
        credentials = Credentials(url=IBM_URL, api_key=IBM_API_KEY)
    client = APIClient(credentials=credentials, project_id=IBM_PROJECT_ID)
    return ModelInference(
        model_id="meta-llama/llama-3-3-70b-instruct",
        api_client=client,
        params={
            "decoding_method": "greedy",
            "max_new_tokens": 2048,
            "min_new_tokens": 50,
            "repetition_penalty": 1.1,
            "temperature": 0.7,
        },
    )

# ── Prompt builder ────────────────────────────────────────────────────────────
def build_system_prompt(mode: str, profile: dict) -> str:
    budget_key   = profile.get("budget", AGENT_INSTRUCTIONS["default_budget"])
    budget_info  = AGENT_INSTRUCTIONS["budget_tiers"].get(budget_key, AGENT_INSTRUCTIONS["budget_tiers"]["moderate"])
    group_type   = profile.get("group_type", AGENT_INSTRUCTIONS["default_group"])
    trip_style   = profile.get("trip_style", AGENT_INSTRUCTIONS["default_trip_style"])
    travelers    = profile.get("travelers", 2)
    children     = profile.get("children", 0)

    base = (
        f"{AGENT_INSTRUCTIONS['persona']}\n\n"
        f"TRAVELER PROFILE:\n"
        f"  • Group: {group_type} ({travelers} adults, {children} children)\n"
        f"  • Budget tier: {budget_info['label']} "
        f"(Hotels: {budget_info['hotel_range']}, Food: {budget_info['daily_food']}, "
        f"Transport: {budget_info['transport']})\n"
        f"  • Trip style: {trip_style}\n\n"
        f"OUTPUT RULES:\n{AGENT_INSTRUCTIONS['output_rules']}\n\n"
        f"SAFETY:\n{AGENT_INSTRUCTIONS['safety_note']}\n"
    )

    mode_instructions = {
        "chat": (
            "MODE: Conversational AI Travel Assistant.\n"
            "Answer questions concisely yet thoroughly. Keep responses under 400 words unless a full itinerary is requested."
        ),
        "itinerary": (
            "MODE: Smart Itinerary Generator.\n"
            "Generate a detailed day-by-day itinerary. Include specific place names, timings, costs, "
            "hotel recommendations, restaurant/café picks, and a nightly estimated cost total."
        ),
        "budget": (
            "MODE: Budget Dashboard Analyst.\n"
            "Produce a detailed cost breakdown in JSON format with these exact keys: "
            "accommodation, food, transport, activities, shopping, miscellaneous, total_estimated. "
            "All values must be numbers (USD). Also include a 'savings_tips' array with 3–5 tips."
        ),
        "recommendations": (
            "MODE: Destination Recommender.\n"
            "Suggest 5 hidden-gem destinations matching the user's profile. For each include: "
            "name, country, best_time, why_visit, avg_cost_per_day (USD), safety_rating (1-5)."
        ),
    }
    return base + "\n" + mode_instructions.get(mode, mode_instructions["chat"])


def call_watsonx(prompt: str) -> str:
    try:
        model  = get_watsonx_model()
        result = model.generate_text(prompt=prompt)
        return result
    except Exception as exc:
        return f"[Watsonx Error] {str(exc)}"


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()
    profile = data.get("profile", {})
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "message is required"}), 400

    system_prompt = build_system_prompt("chat", profile)

    # Build conversation context (last 6 turns)
    conversation = "\n".join(
        f"{'User' if h['role'] == 'user' else 'Voyager AI'}: {h['content']}"
        for h in history[-6:]
    )

    full_prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"{conversation}\n"
        f"User: {message}\n"
        f"Voyager AI:"
    )

    response = call_watsonx(full_prompt)
    return jsonify({"response": response, "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    data        = request.get_json(force=True)
    destination = data.get("destination", "").strip()
    days        = int(data.get("days", 5))
    profile     = data.get("profile", {})

    if not destination:
        return jsonify({"error": "destination is required"}), 400

    system_prompt = build_system_prompt("itinerary", profile)
    full_prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"User: Create a {days}-day travel itinerary for {destination}. "
        f"Include hotels, restaurants, cafés, activities, and daily cost estimates.\n"
        f"Voyager AI:"
    )

    response = call_watsonx(full_prompt)
    return jsonify({"itinerary": response, "destination": destination, "days": days})


@app.route("/api/budget", methods=["POST"])
def api_budget():
    data        = request.get_json(force=True)
    destination = data.get("destination", "").strip()
    days        = int(data.get("days", 5))
    profile     = data.get("profile", {})

    if not destination:
        return jsonify({"error": "destination is required"}), 400

    system_prompt = build_system_prompt("budget", profile)
    full_prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"User: Provide a budget breakdown JSON for a {days}-day trip to {destination} "
        f"for {profile.get('travelers', 2)} adults and {profile.get('children', 0)} children. "
        f"Budget tier: {profile.get('budget', 'moderate')}.\n"
        f"Voyager AI:"
    )

    raw = call_watsonx(full_prompt)

    # Try to parse JSON block from response
    budget_data = None
    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            budget_data = json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        budget_data = None

    return jsonify({"raw": raw, "budget": budget_data, "destination": destination, "days": days})


@app.route("/api/recommendations", methods=["POST"])
def api_recommendations():
    data    = request.get_json(force=True)
    profile = data.get("profile", {})
    query   = data.get("query", "Suggest destinations for me")

    system_prompt = build_system_prompt("recommendations", profile)
    full_prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"User: {query}\n"
        f"Voyager AI:"
    )

    response = call_watsonx(full_prompt)
    return jsonify({"recommendations": response})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": "ibm/granite-3-3-8b-instruct",
        "agent": "Voyager AI",
        "timestamp": datetime.utcnow().isoformat(),
    })


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print(f"\n🌍 Voyager AI Travel Planner — running on http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)