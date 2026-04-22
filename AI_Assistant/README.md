# A2A (Agent-to-Agent) Coordination Framework

Welcome to the **A2A Coordination Framework Case Study**. This project demonstrates a production-grade, multi-agent architecture where a central Coordinator Assistant dynamically routes natural language queries to specialized, independent sub-agents hosted across different cloud platforms.

## 🚀 Overview

The A2A Framework is designed to break down complex user requests and delegate them to domain-specific AI agents. Instead of relying on a monolithic LLM prompt to do everything, the system acts as a router—intelligently discovering capabilities, negotiating protocols (JSON-RPC vs REST), and enforcing secure server-to-server communication.

### Key Capabilities
- **Dynamic Task Delegation:** The central coordinator uses an LLM to analyze user intent and automatically selects the most appropriate specialized agent.
- **Protocol Agnostic:** Seamlessly communicates with remote agents via standardized `JSON-RPC` or native `REST` APIs.
- **Secure Authentication:** Implements robust secret-based authentication (Bearer Tokens & custom Headers) to ensure only authorized coordinators can trigger remote agents.
- **Full-Stack Interface:** Includes a modern React/Vite frontend equipped with real-time SSE (Server-Sent Events) streaming, file uploads, and markdown rendering.
- **Evaluation & Benchmarking:** Built-in evaluation scripts (`run_a2a_eval.py`) to measure delegation accuracy, execution success, and token consumption using GAIA-style metrics.

## 🏗 Architecture

The project is split into the following primary components:

### 1. Coordinator Backend (FastAPI)
Located in `AI_Assistant/app`, this is the brain of the system.
- Exposes API endpoints for the frontend.
- Maintains an Agent Registry (`discovery.py`) detailing available agents and their connection schemas.
- Executes `rpc_client.py` to securely communicate with remote agents.

### 2. Specialized Remote Agents
The coordinator delegates tasks to cloud-hosted specialized agents:
- **📊 Data Analyst Agent:** Handles CSV file uploads and executes Python Pandas queries. Communicates via `JSON-RPC`.
- **🏋️ Fitness Agent:** Answers domain-specific health and workout queries. Communicates via `REST`.
- **⚽ Football Reporter Agent:** Generates real-time football insights and tweets based on specific personas. Communicates via `REST`.

### 3. Frontend UI (React + Vite)
Located in `AI_Assistant/frontend`, providing a sleek, interactive user interface.
- Supports chat history, real-time typing indicators, and file attachments.
- Connects to the coordinator securely via `VITE_APP_API_KEY`.

---

## 🛠️ Local Development & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai/) API key (for the LLM)

### 1. Backend Setup

Navigate to the `AI_Assistant` directory:
```bash
cd AI_Assistant
```

Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Configure your `.env` file in the `AI_Assistant` root directory. Ensure you have the necessary tokens to connect to your remote agents:
```env
# AI_Assistant/.env
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
APP_API_KEY=test-secret-key

# Remote Agent Auth Tokens
FOOTBALL_REPORTER_AUTH_TOKEN=your_football_token
DS_AGENT_BEARER_TOKEN=your_ds_token
FITNESS_AGENT_BEARER_TOKEN=your_fitness_token
```

Run the FastAPI Coordinator:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd AI_Assistant/frontend
```

Install Node dependencies:
```bash
npm install
```

Set up the frontend `.env` file (`AI_Assistant/frontend/.env`):
```env
VITE_APP_API_KEY=test-secret-key
```

Run the React development server:
```bash
npm run dev
```

Visit `http://localhost:5173` in your browser to interact with the A2A Assistant.

---

## 🧪 Evaluation & Testing

To evaluate the performance of the agent delegation, run the evaluation suite:

```bash
cd AI_Assistant
python eval/run_a2a_eval.py
```
This script tests various edge cases (e.g., routing a fitness question vs a football question) and generates a report on routing accuracy and token utilization.

---

## 🔒 Security Practices

- **Zero Hardcoded Secrets:** All frontend and backend API keys are securely loaded via `.env`.
- **Strict Headers:** The RPC client strictly requires matched authentication tokens before communicating with off-server agents, preventing unauthorized prompt injection and unauthorized usage of cloud endpoints.

## 📜 License
MIT License
