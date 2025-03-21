from flask import Flask, request, jsonify, render_template
import openai
import sqlite3
import logging
import stripe
import os
from flask_babel import Babel, _

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
babel = Babel(app)
stripe.api_key = "tu_api_key_de_stripe"

# Configuración de logging
def configurar_logger():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Generación de contenido con OpenAI
def generar_contenido(prompt, modelo="gpt-4"):
    try:
        respuesta = openai.ChatCompletion.create(
            model=modelo,
            messages=[{"role": "system", "content": "Eres un asistente de IA experto en negocios."},
                      {"role": "user", "content": prompt}]
        )
        return respuesta["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error generando contenido: {str(e)}")
        return None

# Inicializar base de datos SQLite
def inicializar_bd():
    conexion = sqlite3.connect("usuarios.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            email TEXT UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            monto REAL,
            status TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)
    conexion.commit()
    conexion.close()

# Registrar usuario en la base de datos
def registrar_usuario(nombre, email):
    try:
        conexion = sqlite3.connect("usuarios.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
        conexion.commit()
        conexion.close()
        return {"status": "success", "message": "Usuario registrado correctamente"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Procesar pago con Stripe
def procesar_pago(email, monto):
    try:
        conexion = sqlite3.connect("usuarios.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        if usuario:
            charge = stripe.Charge.create(
    amount=int(monto * 100),
    currency="usd",
    source="tok_visa",
    description=f"Pago de {email} por ${monto}"
)

         
