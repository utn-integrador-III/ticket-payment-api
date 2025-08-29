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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Esquemas para Driver (Chofer)
class DriverLoginRequest(BaseModel):
    email: str
    password: str

class DriverRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    license_number: str
    phone: Optional[str] = None

class DriverProfile(BaseModel):
    id: str
    name: str
    email: str
    license_number: str
    phone: str
    vehicle_info: dict
    assigned_routes: list[str]
    is_active: bool

class VehicleInfo(BaseModel):
    make: str
    model: str
    year: int
    license_plate: str
    color: Optional[str] = None
    capacity: Optional[int] = None

# Esquemas para Route (Ruta)
class RouteCreateRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    origin: str
    destination: str
    stops: Optional[list[str]] = []
    fare_amount: float
    distance_km: Optional[float] = 0.0
    estimated_duration: Optional[int] = 0
    schedule: Optional[dict] = {}

class RouteUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    stops: Optional[list[str]] = None
    fare_amount: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_duration: Optional[int] = None
    schedule: Optional[dict] = None

class RouteProfile(BaseModel):
    id: str
    name: str
    code: str
    description: str
    origin: str
    destination: str
    stops: list[str]
    fare_amount: float
    distance_km: float
    estimated_duration: int
    assigned_drivers: list[str]
    is_active: bool
    schedule: dict

class DriverScanRequest(BaseModel):
    qr_data: str
    route_code: str  # Código de la ruta donde se realiza el cobro

class RouteAssignmentRequest(BaseModel):
    driver_id: str
    route_id: str
