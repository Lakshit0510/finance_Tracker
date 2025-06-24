from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import uvicorn
import os
import pandas as pd
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")
ASI1_URL = "https://api.asi1.ai/v1/chat/completions"

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
class FinancialQuery(BaseModel):
    userid: str
    query: str

class FinancialResponse(BaseModel):
    response: str

# Load transactions from CSV
def load_transactions(csv_path="transactions.csv"):
    abs_path = os.path.join(os.path.dirname(__file__), csv_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")
    df = pd.read_csv(abs_path)
    return df.to_dict(orient="records")

transactions = load_transactions()

# Define financial functions
def spending_breakdown(userid):
    user_transactions = [tx for tx in transactions if tx["userid"] == userid]
    breakdown = {}
    for tx in user_transactions:
        category = tx["class"]
        breakdown[category] = breakdown.get(category, 0) + tx["amount"]
    return json.dumps(breakdown, indent=2)

def largest_expense_category(userid):
    user_transactions = [tx for tx in transactions if tx["userid"] == userid]
    if not user_transactions:
        return "No transactions found."
    category_totals = {}
    for tx in user_transactions:
        category_totals[tx["class"]] = category_totals.get(tx["class"], 0) + tx["amount"]
    largest_category = max(category_totals, key=category_totals.get, default=None)
    return f"Largest expense category: {largest_category} (${category_totals[largest_category]:.2f})"

def total_balance(userid):
    user_transactions = [tx for tx in transactions if tx["userid"] == userid]
    balance = sum(tx["amount"] for tx in user_transactions)
    return f"Total balance: ${balance:.2f}"

# Function dispatcher
def determine_function_call(query, userid):
    function_map = {
        "spending breakdown": spending_breakdown,
        "largest expense category": largest_expense_category,
        "total balance": total_balance
    }
    for key in function_map:
        if key in query.lower():
            return function_map[key](userid)
    return None

# Fetch AI response
def fetch_asi1_response(query, userid):
    transactions_data = format_transactions(userid)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = json.dumps({
        "model": "asi1-mini",
        "messages": [
            {"role": "system", "content": "You are a financial assistant."},
            {"role": "user", "content": f"{query}\n\n{transactions_data}"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    })
    response = requests.post(ASI1_URL, headers=headers, data=payload)
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error fetching response")

# Format transactions for LLM
def format_transactions(userid):
    user_transactions = [tx for tx in transactions if tx["userid"] == userid]
    if not user_transactions:
        return "No transactions found."
    return "\n".join([f"- {tx['time']}: {tx['class']} ${tx['amount']}" for tx in user_transactions])

@app.post("/query")
async def api_query(query: FinancialQuery):
    processed_query = determine_function_call(query.query, query.userid)
    response_text = processed_query if processed_query else fetch_asi1_response(query.query, query.userid)
    return {"response": response_text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
