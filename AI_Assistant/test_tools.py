import os
from dotenv import load_dotenv
load_dotenv()

from app.services.agent_service import query_assistant

print("Test 1: Football")
trace1 = []
print(query_assistant("Generate a hype tweet about the Champions League final", trace1))
print("Trace 1:", trace1)
print("\n" + "-"*40 + "\n")

print("Test 2: Agriculture")
trace2 = []
print(query_assistant("What crops are best to plant in spring in tropical climate?", trace2))
print("Trace 2:", trace2)
print("\n" + "-"*40 + "\n")
