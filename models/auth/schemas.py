from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    payment_method: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    balance: float
    payment_methods: list[dict]

class PaymentMethod(BaseModel):
    card_holder: str
    card_number: str
    expiry: str
    cvv: str

class PaymentMethodIn(PaymentMethod):
    pass

class TopupRequest(BaseModel):
    amount: float
    payment_method_id: str

class ScanRequest(BaseModel):
    qr_data: str
    amount: float
