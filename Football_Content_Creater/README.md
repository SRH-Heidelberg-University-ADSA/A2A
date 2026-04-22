# ⚽ Football VAR Agent: Multi-Agent Orchestration Pipeline

An autonomous AI microservice designed to act as a Virtual Assistant Referee (VAR) and Content Creator. This project demonstrates an enterprise-grade **Agentic Workflow**, moving beyond a standard chatbot by utilizing multi-step orchestration, strict security guardrails, and Google's File Search API for 100% accurate rule retrieval.

Built as a headless API for A2A (Agent-to-Agent) communication, with an included Streamlit dashboard for manual testing.

---

## 🧠 System Architecture

Unlike traditional LLMs that rely on pre-trained memory, this agent utilizes a highly structured, 3-step pipeline to ensure factual accuracy and safe outputs:

1. **The Gatekeeper (Security Guardrail):**
   - **Agent:** `guardrail_bot.py`
   - **Function:** Intercepts incoming requests and blocks prompt injections, off-topic queries (e.g., recipes, coding requests), and non-football related prompts before they consume processing power.

2. **The Analyst (Google File Search API):**
   - **Agent:** `rules_bot.py`
   - **Function:** Bypasses the limitations of traditional RAG (chunking errors/semantic gaps) by utilizing Google's File Search API. It loads the entire IFAB rulebook (`football_rules.pdf`) into a massive context window to extract the exact legal ruling for any match event.

3. **The Hype Man (Content Persona):**
   - **Agent:** `content_bot.py`
   - **Function:** Translates the strict legal ruling into engaging, persona-driven social media content (configurable via `personas.json`).

---

## 📁 Core Repository Structure

```
FOOTBALL_CONTENT_CREATOR/
│
├── agents/                     # Multi-agent logic modules
│   ├── content_bot.py          # Social media persona generator
│   ├── guardrail_bot.py        # Security and off-topic filter
│   └── rules_bot.py            # Google File API retrieval agent
│
├── api.py                      # FastAPI backend (A2A endpoint)
├── app.py                      # Streamlit frontend (Interactive UI)
├── setup_knowledge.py          # Script to upload PDF to Google AI Studio
│
├── football_rules.pdf          # The Ground Truth knowledge base
├── personas.json               # Configurable agent personas
├── agent_card.json             # Agent metadata and descriptions
│
├── Dockerfile                  # Containerization configuration
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (Ignored in git)
```

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key
- An OpenRouter API Key (if using external models for guardrails/content)

### 2. Clone and Install
```bash
git clone https://github.com/your-username/football-var-agent.git
cd football-var-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your API keys:

```bash
GEMINI_API_KEY=your_google_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 4. Initialize the Knowledge Base
Before running the agent, you must upload the IFAB rulebook to Google's servers. Run the setup script:

```bash
python setup_knowledge.py
```

Wait for the script to finish processing. It will output a FILE URI (e.g., `files/xxxxxx`). Copy this URI and add it to your `.env` file:

```bash
RULE_FILE_URI=files/your_generated_file_id
```

## 💻 Running the Application

### Start the FastAPI Backend (A2A Server)
This spins up the headless microservice intended for Agent-to-Agent communication.

```bash
uvicorn api:app --reload --port 8000
```

API Documentation (Swagger UI) available at: http://localhost:8000/docs

### Start the Streamlit UI
Open a second terminal window to run the interactive testing dashboard.

```bash
streamlit run app.py
```

UI available at: http://localhost:8501

## 🔌 API Usage (A2A Integration)
To call the agent from another service, send a POST request to the `/generate-tweet` endpoint.

**Endpoint:** `POST /generate-tweet`  
**Headers:** `x-auth-token: GOAL_2026`

**Request Body (JSON):**
```json
{
  "event_description": "A defender aggressively slides in with two feet from behind, missing the ball.",
  "persona": "analyst"
}
```

**Successful Response (200 OK):**
```json
{
  "status": "success",
  "ruling": "VERDICT: Direct free kick or penalty kick. REASONING: The player should be sent off (red card) for serious foul play.",
  "tweet": "🚨 RED CARD ALERT! 🚨 Two feet from behind? That's an early shower! Direct free kick awarded. #Football #VAR"
}
```

**Guardrail Blocked Response (200 OK):**
```json
{
  "status": "blocked",
  "reason": "Topic is not related to Football."
}
```