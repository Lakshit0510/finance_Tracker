# --- IMPORTS ---
import os
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Float, Integer, String, func, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# --- INITIAL SETUP & CONFIG ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY") # For the external AI service
AI_SERVICE_URL = "https://api.asi1.ai/v1/chat/completions" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or not SECRET_KEY:
    raise ValueError("DATABASE_URL and SECRET_KEY must be set in the .env file")

# --- DATABASE SETUP ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SECURITY SETUP ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- DATABASE MODELS ---
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class TransactionDB(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    userid = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    class_name = Column("class", String, nullable=False)
    time = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# --- PYDANTIC SCHEMAS ---
class UserBase(BaseModel): username: str
class UserCreate(UserBase): password: str
class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel): access_token: str; token_type: str
class TokenData(BaseModel): username: Optional[str] = None

class TransactionBase(BaseModel):
    amount: float
    class_name: str
    time: str
class TransactionCreate(TransactionBase): pass
class Transaction(TransactionBase):
    id: int
    userid: str
    class Config:
        from_attributes = True

class PlotData(BaseModel):
    labels: List[str]
    data: List[float]

class QueryRequest(BaseModel):
    query: str

# --- SECURITY & CRUD FUNCTIONS ---
def verify_password(p, h): return pwd_context.verify(p, h)
def get_password_hash(p): return pwd_context.hash(p)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
def get_user(db: Session, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()
def create_user(db: Session, user: UserCreate):
    hp = get_password_hash(user.password)
    db_u = UserDB(username=user.username, hashed_password=hp)
    db.add(db_u)
    db.commit()
    db.refresh(db_u)
    return db_u
def db_create_transaction(db: Session, transaction: TransactionCreate, userid: str):
    db_transaction = TransactionDB(**transaction.dict(), userid=userid)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
def db_get_transactions_by_user(db: Session, userid: str):
    return db.query(TransactionDB).filter(TransactionDB.userid == userid).all()
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    cred_exc = HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username: raise cred_exc
    except JWTError: raise cred_exc
    user = get_user(db, username)
    if not user: raise cred_exc
    return user

# --- LOCAL QUERY HANDLER FUNCTIONS ---
def spending_breakdown(userid: str, db: Session):
    query_result = db.query(TransactionDB.class_name, func.sum(TransactionDB.amount)).filter(TransactionDB.userid == userid).group_by(TransactionDB.class_name).all()
    if not query_result: return "No spending transactions found."
    breakdown = {category: total for category, total in query_result}
    return "Spending Breakdown:\n" + "\n".join([f"- {c}: ${t:.2f}" for c, t in breakdown.items()])

def total_spending(userid: str, db: Session):
    total = db.query(func.sum(TransactionDB.amount)).filter(TransactionDB.userid == userid).scalar()
    return f"Your total spending across all transactions is ${total or 0:.2f}."

def determine_function_call(query: str, userid: str, db: Session):
    query = query.lower()
    function_map = {
        "spending breakdown": spending_breakdown,
        "total spending": total_spending,
    }
    for keyword, func in function_map.items():
        if keyword in query:
            return func(userid, db)
    return None

# --- AI FALLBACK FUNCTION  ---
def fetch_llm_response(query: str, userid: str, db: Session):
    if not API_KEY:
        return "AI service is not configured. Please set the API_KEY in your .env file."

    transactions = db_get_transactions_by_user(db, userid)
    transaction_summary = "\n".join([f"- {tx.time}: {tx.class_name} ${tx.amount}" for tx in transactions])
    
    system_prompt = "You are a helpful financial assistant. Analyze the user's query and the provided transaction data to give a clear and concise answer.Do no end with followup questions."
    user_prompt = f"User Query: \"{query}\"\n\nHere is my transaction history:\n{transaction_summary}"
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "asi1-mini", # This is a placeholder model name, change if needed
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    try:
        response = requests.post(AI_SERVICE_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error connecting to the AI service: {e}"
    except (KeyError, IndexError):
        return "Received an unexpected or malformed response from the AI service."

# --- FASTAPI APP & ENDPOINTS ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- AUTHENTICATION ENDPOINTS ---
@app.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, user.username): raise HTTPException(400, "Username already registered")
    return create_user(db=db, user=user)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password", {"WWW-Authenticate": "Bearer"})
    access_token = create_access_token({"sub": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# --- PROTECTED QUERY ENDPOINT (with AI Fallback) ---
@app.post("/query", response_model=dict)
async def api_query(request: QueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    userid = current_user.username
    # Step 1: Check for a local, pre-defined function match
    local_response = determine_function_call(request.query, userid, db)
    if local_response:
        return {"response": local_response}
    # Step 2: If no match, fall back to the AI service
    ai_response = fetch_llm_response(request.query, userid, db)
    return {"response": ai_response}

# --- OTHER PROTECTED DATA ENDPOINTS ---
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Fetches all transactions for the currently authenticated user."""
    return db_get_transactions_by_user(db, current_user.username)

@app.delete("/transactions/{transaction_id}", response_model=dict)
async def delete_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Deletes a specific transaction by its ID, ensuring it belongs to the user."""
    transaction_to_delete = db.query(TransactionDB).filter(TransactionDB.id == transaction_id).first()
    
    if not transaction_to_delete:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction_to_delete.userid != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this transaction")
        
    db.delete(transaction_to_delete)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}

@app.delete("/users/me", response_model=dict)
async def delete_user_and_transactions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Deletes the currently authenticated user and all of their associated transactions."""
    userid_to_delete = current_user.username
    
    db.query(TransactionDB).filter(TransactionDB.userid == userid_to_delete).delete(synchronize_session=False)
    db.query(UserDB).filter(UserDB.username == userid_to_delete).delete(synchronize_session=False)
    db.commit()
    
    return {"message": f"User {userid_to_delete} and all data have been deleted."}

@app.post("/add_transaction", response_model=Transaction)
async def add_transaction(transaction: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db_create_transaction(db=db, transaction=transaction, userid=current_user.username)

@app.get("/plot/spending_by_category", response_model=PlotData)
async def get_spending_by_category(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query_result = db.query(TransactionDB.class_name, func.sum(TransactionDB.amount)).filter(TransactionDB.userid == current_user.username).group_by(TransactionDB.class_name).all()
    if not query_result: return {"labels": [], "data": []}
    return {"labels": [item[0] for item in query_result], "data": [item[1] for item in query_result]}

@app.get("/plot/spending_over_time", response_model=PlotData)
async def get_spending_over_time(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query_result = db.query(TransactionDB.time, func.sum(TransactionDB.amount)).filter(TransactionDB.userid == current_user.username).group_by(TransactionDB.time).order_by(TransactionDB.time).all()
    if not query_result: return {"labels": [], "data": []}
    return {"labels": [item[0] for item in query_result], "data": [item[1] for item in query_result]}