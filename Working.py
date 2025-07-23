from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import requests
import uvicorn
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
API_KEY = os.getenv("API_KEY")


ASI1_URL = "https://api.asi1.ai/v1/chat/completions" 

app = FastAPI()


origins = [
    
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class FinancialQuery(BaseModel):
    userid: str
    query: str

class FinancialResponse(BaseModel):
    response: str

class Transaction(BaseModel):
    userid: str
    amount: float
    class_name: str
    time: str

class PlotData(BaseModel):
    labels: list
    data: list

# --- Data Loading and Management ---
TRANSACTIONS_CSV_PATH = "transactions.csv"

def load_transactions(csv_path=TRANSACTIONS_CSV_PATH):
    if not os.path.exists(csv_path):
        pd.DataFrame(columns=['userid', 'time', 'class', 'amount']).to_csv(csv_path, index=False)
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")

transactions = load_transactions()

def save_transaction_to_csv(transaction: Transaction):
    df = pd.DataFrame([transaction.dict(by_alias=True)])
    df.rename(columns={'class_name': 'class'}, inplace=True)
    df.to_csv(TRANSACTIONS_CSV_PATH, mode='a', header=not os.path.exists(TRANSACTIONS_CSV_PATH), index=False)


# --- API Endpoints ---
@app.get("/get_users")
async def get_users():
    if not transactions:
        return {"users": []}
    df = pd.DataFrame(transactions)
    unique_users = df['userid'].unique().tolist()
    return {"users": unique_users}

@app.post("/add_transaction")
async def add_transaction(transaction: Transaction):
    try:
        new_tx_memory = {
            "userid": transaction.userid,
            "amount": transaction.amount,
            "class": transaction.class_name,
            "time": transaction.time
        }
        transactions.append(new_tx_memory)
        save_transaction_to_csv(transaction)
        return {"message": "Transaction added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=FinancialResponse)
async def api_query(query: FinancialQuery):
    local_response = determine_function_call(query.query, query.userid)
    if local_response:
        response_text = local_response
    else:
        response_text = fetch_llm_response(query.query, query.userid)
    return {"response": response_text}

# --- NEW: Plotting Endpoints ---
@app.get("/plot/spending_by_category", response_model=PlotData)
async def get_spending_by_category(userid: str):
    """
    Processes transaction data to return spending totals per category.
    Perfect for a pie or bar chart.
    """
    user_transactions = get_user_transactions(userid)
    if not user_transactions:
        return {"labels": [], "data": []}
    
    df = pd.DataFrame(user_transactions)
    category_summary = df.groupby('class')['amount'].sum().sort_values(ascending=False)
    
    return {
        "labels": category_summary.index.tolist(),
        "data": category_summary.values.tolist()
    }

@app.get("/plot/spending_over_time", response_model=PlotData)
async def get_spending_over_time(userid: str):
    """
    Processes transaction data to return total spending per day.
    Perfect for a line chart.
    """
    user_transactions = get_user_transactions(userid)
    if not user_transactions:
        return {"labels": [], "data": []}

    df = pd.DataFrame(user_transactions)
    df['time'] = pd.to_datetime(df['time'], format='mixed')
    
    daily_summary = df.groupby(df['time'].dt.date)['amount'].sum().sort_index()

    return {
        "labels": [date.strftime('%Y-%m-%d') for date in daily_summary.index],
        "data": daily_summary.values.tolist()
    }

# --- Financial Functions & Function Dispatcher ---
def get_user_transactions(userid: str):
    return [tx for tx in transactions if tx["userid"] == userid]

def spending_breakdown(userid: str):
    user_transactions = get_user_transactions(userid)
    if not user_transactions: return "No transactions found."
    breakdown = {}
    for tx in user_transactions:
        breakdown[tx["class"]] = breakdown.get(tx["class"], 0) + tx["amount"]
    formatted_breakdown = "Spending Breakdown:\n" + "\n".join([f"- {cat}: ${total:.2f}" for cat, total in breakdown.items()])
    return formatted_breakdown

def largest_expense_category(userid: str):
    user_transactions = get_user_transactions(userid)
    if not user_transactions: return "No transactions found."
    category_totals = {}
    for tx in user_transactions:
        category_totals[tx["class"]] = category_totals.get(tx["class"], 0) + tx["amount"]
    largest_category = max(category_totals, key=category_totals.get)
    return f"Your largest expense category is '{largest_category}' with a total of ${category_totals[largest_category]:.2f}."

def total_spending(userid: str):
    user_transactions = get_user_transactions(userid)
    if not user_transactions: return "No transactions found."
    total = sum(tx["amount"] for tx in user_transactions)
    return f"Your total spending across all transactions is ${total:.2f}."

def determine_function_call(query: str, userid: str):
    query = query.lower()
    function_map = {
        "spending breakdown": spending_breakdown,
        "largest expense category": largest_expense_category,
        "total spending": total_spending,
        "total balance": total_spending
    }
    for keyword, func in function_map.items():
        if keyword in query:
            return func(userid)
    return None

# --- AI Model Integration ---
def fetch_llm_response(query: str, userid: str):
    if not API_KEY: return "API_KEY is not configured. Please set it in your .env file."
    user_transactions = get_user_transactions(userid)
    transactions_summary = "\n".join([f"- {tx['time']}: {tx['class']} ${tx['amount']}" for tx in user_transactions])
    system_prompt = "You are a helpful and friendly financial assistant. Analyze the user's query and the provided transaction data to give a clear and concise answer."
    user_prompt = f"User Query: \"{query}\"\n\nHere is the user's transaction history:\n{transactions_summary}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": "asi1-mini", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.7, "max_tokens": 500}
    try:
        response = requests.post(ASI1_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't get a response.")
    except requests.exceptions.RequestException as e:
        return f"Error connecting to the AI service: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
