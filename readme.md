# 🤖 Vendor Assignment & Communication AI Agent

This project is a proof-of-concept (POC) for building an intelligent backend AI agent that performs **vendor selection** and **personalized communication drafting** for customer service tasks (e.g., booking a cab, finding a plumber, etc.). It's powered by a combination of **FastAPI** for API services and **Streamlit** for a simple and interactive frontend.

---

## 📌 Problem Statement

Customer tasks like hotel booking or urgent repairs are handled by backend agents, who in turn coordinate with vendors. This AI agent helps:

1. 🧠 **Select the most suitable vendor** based on task requirements.
2. ✉️ **Draft a personalized message** to the vendor in their preferred communication style.

---

## ⚙️ Tech Stack

- **Python 3.9+**
- **FastAPI** – backend API for vendor selection and message generation
- **Streamlit** – frontend interface to simulate task entry and vendor interaction
- **Uvicorn** – ASGI server for FastAPI
- **Google Generative LLM** – for task interpretation and message generation

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/vendor-ai-agent.git
cd vendor-ai-agent
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
```

Install the required packages

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a .env file in the root directory and add the following

```sh
OPENAI_API_KEY=your_openai_api_key
```

### 4. Run the Backend

Start the FastAPI server

```bash
uvicorn main:app --reload
```

### 5. Run the Frontend (Streamlit)

In a new terminal, navigate to the project directory and run:

```bash
streamlit run frontend.py
```

## Mock Data Format

### Vendor Sample

```json
{
    "vendor_id": "V001",
    "name": "Rapid Plumbers",
    "category_expertise": ["repairs", "plumbing"],
    "response_time_hours": 1,
    "preferred_communication_style": "casual",
    "past_reliability_score": 4.8,
    "constraints": ["Only serves downtown area", "Requires 2hr lead time for non-urgent tasks"]
}
```

### Task Sample

```json
{
    "task_id": "T101",
    "task_description": "I need a plumber urgently for a leaking tap in the kitchen.",
    "category": "plumbing",
    "urgency": "high",
    "special_requirements": "Need someone who can bring spare parts for standard faucet types."
}
```
