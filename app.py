from flask import Flask, request, jsonify
import stripe
import openai
import os
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

# Inicializar base de datos y JWT
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Configurar API Keys
openai.api_key = os.getenv('OPENAI_API_KEY')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Crear base de datos
with app.app_context():
    db.create_all()

# Ruta de registro
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    new_user = User(email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuario registrado con éxito'})

# Ruta de login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if not user:
        return jsonify({'message': 'Credenciales incorrectas'}), 401
    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token)

# Ruta para generar video con IA
@app.route('/generate-video', methods=['POST'])
@jwt_required()
def generate_video():
    data = request.json
    prompt = data.get('prompt', 'Crea un video increíble con IA')
    response = openai.ChatCompletion.create(
        model='gpt-4', messages=[{'role': 'user', 'content': prompt}]
    )
    return jsonify({'video_url': 'https://fakevideo.com/video.mp4', 'description': response['choices'][0]['message']['content']})

# Ruta de pago con Stripe
@app.route('/pay', methods=['POST'])
@jwt_required()
def pay():
    data = request.json
    intent = stripe.PaymentIntent.create(
        amount=1000,  # Monto en centavos (10 USD)
        currency='usd',
        payment_method=data['payment_method_id'],
        confirm=True
    )
    return jsonify({'message': 'Pago exitoso', 'payment_intent': intent.id})

if __name__ == '__main__':
    app.run(debug=True)
