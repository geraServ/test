from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pytonconnect import TonConnect
import uuid
import os

from models import User, Base
from database import engine, SessionLocal

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Настраиваем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

# Инициализация TonConnect
MANIFEST_URL = "https://geraserv.github.io/tonconnect-manifest.json"
connector = TonConnect(MANIFEST_URL)

# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    # Получаем или создаем пользователя
    init_data = request.query_params.get("tgWebAppData", "")
    user_id = extract_user_id_from_init_data(init_data) if init_data else str(uuid.uuid4())
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Проверяем подключен ли кошелек
    wallet_connected = bool(user.wallet_address)
    
    # Генерируем ссылку для подключения кошелька
    connection_url = None
    wallets_list = TonConnect.get_wallets()
    if not wallet_connected:
        connection_url = await connector.connect(wallets_list[0])
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "wallet_connected": wallet_connected,
            "wallet_address": user.wallet_address if wallet_connected else None,
            "connection_url": connection_url,
            "balance": "0"  # Здесь будет реальный баланс после реализации
        }
    )

@app.get("/connect-wallet")
async def connect_wallet(
    request: Request,
    account: str,
    db: Session = Depends(get_db)
):
    # Получаем пользователя
    init_data = request.query_params.get("tgWebAppData", "")
    user_id = extract_user_id_from_init_data(init_data) if init_data else None
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    # Обновляем адрес кошелька в базе данных
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.wallet_address = account
        db.commit()
    
    return {"status": "success"}

def extract_user_id_from_init_data(init_data: str) -> str:
    # Здесь должна быть логика извлечения user_id из initData Telegram WebApp
    # Это упрощенная версия, в реальном приложении нужно проверять подпись
    from urllib.parse import parse_qs
    params = parse_qs(init_data)
    return params.get('user', {}).get('id', str(uuid.uuid4()))

