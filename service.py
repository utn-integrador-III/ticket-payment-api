from flask_restful import Api
from controllers.auth.controller import AuthController
from controllers.user.controller import UserQRController
from controllers.payment.controller import PaymentController, PaymentMethodController
from controllers.wallet.controller import WalletController

def add_service_layer(api: Api):
    # Authentication
    api.add_resource(AuthController, '/register', endpoint='register')
    api.add_resource(AuthController, '/login', endpoint='login')
    api.add_resource(AuthController, '/change-password', endpoint='change_password')
    
    # User
    api.add_resource(UserQRController, '/user/qr', endpoint='user_qr')
    
    # Payment
    api.add_resource(PaymentController, '/payment/scan', endpoint='payment_scan')
    api.add_resource(PaymentMethodController, '/payment-methods', endpoint='payment_methods')
    api.add_resource(PaymentMethodController, '/payment-methods/<string:method_id>', 
                     endpoint='payment_method')
    
    # Wallet
    api.add_resource(WalletController, '/wallet/topup', endpoint='wallet_topup')
