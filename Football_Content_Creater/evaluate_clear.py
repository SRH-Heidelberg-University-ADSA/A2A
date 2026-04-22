import json
import os
import requests
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# --- CONFIGURATION ---
AGENT_API_URL = "http://127.0.0.1:8000/generate-tweet" 
AGENT_PASSWORD = "GOAL_2026"

load_dotenv()
# OpenRouter Setup
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
# Using a free model on OpenRouter to save you money!
JUDGE_MODEL = "meta-llama/llama-3.2-3b-instruct"

def run_clear_evaluation():
    print("\n🚀 STARTING 2026 CLEAR STANDARD EVALUATION 🚀\n")
    
    # ---------------------------------------------------------
    # 1. ASSURANCE (Security Test)
    # ---------------------------------------------------------
    print("🔒 Testing ASSURANCE (Security)...")
    try:
        # Intentionally leaving out the headers/password
        res_auth = requests.post(AGENT_API_URL, json={"event_description": "test", "persona": "analyst"})
        if res_auth.status_code == 401:
            assurance_score = "PASS (401 Unauthorized Blocked Intruder)"
        else:
            assurance_score = "FAIL (Allowed unauthorized access)"
    except Exception as e:
        assurance_score = "FAIL (Server Error)"
    print(f"Result: {assurance_score}\n")
    time.sleep(2)

    # ---------------------------------------------------------
    # 2. RELIABILITY (Consistency Test)
    # ---------------------------------------------------------
    print("🔄 Testing RELIABILITY (Consistency)...")
    reliability_test_prompt = "A defender aggressively slides in with two feet from behind."
    headers = {"x-auth-token": AGENT_PASSWORD}
    payload = {"event_description": reliability_test_prompt, "persona": "analyst"}
    
    answers = []
    for i in range(3):
        print(f"  -> Running consistency check {i+1}/3...")
        res = requests.post(AGENT_API_URL, json=payload, headers=headers)
        try:
            # Try to grab the JSON, fallback to error text if it fails
            res_json = res.json()
            # Grab just the first 15 characters to allow for slight AI phrasing changes
            ruling_snippet = str(res_json.get("ruling", ""))[:15] 
        except:
            ruling_snippet = "API_CRASH"
            
        answers.append(ruling_snippet)
        
        # 👇 Massive 15-second pause to prevent rate limits!
        time.sleep(15)
        
    if answers[0] == answers[1] == answers[2] and "API_CRASH" not in answers:
        reliability_score = "PASS (100% Consistent Output)"
    else:
        reliability_score = "FAIL (Outputs varied between runs)"
    print(f"Result: {reliability_score}\n")
    time.sleep(5)

    # ---------------------------------------------------------
    # 3. COST, LATENCY, and EFFICACY (Benchmark Loop)
    # ---------------------------------------------------------
    print("⏱️ Testing COST, LATENCY, and EFFICACY (LLM Judge)...")
    with open("benchmark.json", "r") as file:
        tests = json.load(file)

    metrics = []

    for test in tests:
        print(f"\nProcessing: {test['category']}...")
        payload = {"event_description": test["input_event"], "persona": "analyst"}
        
        # Start Latency Timer
        start_time = time.time()
        
        # Call Agent
        response = requests.post(AGENT_API_URL, json=payload, headers=headers)
        end_time = time.time()
        
        # Calculate Latency
        latency = round(end_time - start_time, 2)
        
        try:
            agent_output = response.json()
            agent_ruling = agent_output.get("ruling", str(agent_output))
        except Exception as e:
            print(f"  ⚠️ Warning: API did not return JSON. Raw text: {response.text}")
            agent_ruling = "BLOCKED OR CRASHED"
            agent_output = {}
        
        # Calculate Estimated Cost (Tokens = Words * 1.3)
        total_words = len(test['input_event'].split()) + len(agent_ruling.split())
        est_tokens = int(total_words * 1.3)

        # Calculate Efficacy using OpenRouter Judge
        judge_prompt = f"""
        Ground Truth: {test['ground_truth']}
        Agent's Answer: {agent_ruling}
        Score the Agent's accuracy from 1 to 5. Provide ONLY the integer.
        """
        try:
            judge_response = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": judge_prompt}]
            )
            efficacy_score = judge_response.choices[0].message.content.strip()
        except:
            efficacy_score = "Error"

        metrics.append({
            "Category": test["category"],
            "Cost": f"~{est_tokens} tokens",
            "Latency": f"{latency}s",
            "Efficacy": f"{efficacy_score}/5"
        })
        
        print("Sleeping 5 seconds to protect local resources...")
        time.sleep(5)

    # ---------------------------------------------------------
    # 4. FINAL REPORT GENERATION
    # ---------------------------------------------------------
    print("\n" + "="*70)
    print(" 🏆 FINAL CLEAR STANDARD EVALUATION REPORT 🏆")
    print("="*70)
    print(f"🔒 ASSURANCE:   {assurance_score}")
    print(f"🔄 RELIABILITY: {reliability_score}")
    print("-" * 70)
    print(f"{'Test Category':<20} | {'Cost (Tokens)':<15} | {'Latency':<10} | {'Efficacy'}")
    print("-" * 70)
    for m in metrics:
        print(f"{m['Category']:<20} | {m['Cost']:<15} | {m['Latency']:<10} | {m['Efficacy']}")
    print("="*70)

    return metrics

if __name__ == "__main__":
    metrics = run_clear_evaluation()

    # ---------------------------------------------------------
    # 5. EXPORT FOR DASHBOARDS
    # ---------------------------------------------------------
    print("\n💾 Exporting data to clear_metrics.csv...")
    
    # Clean up the data slightly for the graphs
    for m in metrics:
        m['Latency (Seconds)'] = float(m['Latency'].replace('s', ''))
        m['Efficacy Score'] = int(m['Efficacy'].split('/')[0]) # Grabs just the number
        m['Cost (Tokens)'] = int(m['Cost'].replace('~', '').replace(' tokens', ''))

    df = pd.DataFrame(metrics)
    # Drop the old string columns so the graphs only get clean numbers
    df = df[['Category', 'Latency (Seconds)', 'Efficacy Score', 'Cost (Tokens)']] 
    df.to_csv("clear_metrics.csv", index=False)
    
    print("✅ Export complete! Ready for visualization.")