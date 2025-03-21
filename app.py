import os
import logging
import sqlite3
import stripe
import openai
from flask import Flask, request, jsonify, render_template
from flask_babel import Babel, _

# Configuración de Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
babel = Babel(app)

# Configuración segura de las API Keys
stripe.api_key = os.getenv("STRIPE_API_KEY", "tu_api_key_de_stripe")
openai.api_key = os.getenv("OPENAI_API_KEY", "tu_api_key_de_openai")

# Configuración de logging
def configurar_logger():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
configurar_logger()

# Generación de contenido con OpenAI
def generar_contenido(prompt, modelo="gpt-4"):
    try:
        respuesta = openai.ChatCompletion.create(
            model=modelo,
            messages=[
                {"role": "system", "content": "Eres un asistente de IA experto en negocios."},
                {"role": "user", "content": prompt}
            ]
        )
        return respuesta["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error generando contenido: {str(e)}")
        return None

# Inicializar base de datos SQLite
def inicializar_bd():
    try:
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
    except Exception as e:
        logging.error(f"Error inicializando BD: {str(e)}")
    finally:
        if conexion:
            conexion.close()

# Registrar usuario en la base de datos
def registrar_usuario(nombre, email):
    try:
        conexion = sqlite3.connect("usuarios.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
        conexion.commit()
        return {"status": "success", "message": "Usuario registrado correctamente"}
    except Exception as e:
        logging.error(f"Error registrando usuario: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()

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
                description=f"Pago de {email}",
                source="tok_visa"
            )
            cursor.execute("INSERT INTO pagos (usuario_id, monto, status) VALUES (?, ?, ?)", (usuario[0], monto, charge.status))
            conexion.commit()
            return {"status": "success", "message": "Pago procesado correctamente"}
        else:
            return {"status": "error", "message": "Usuario no encontrado"}
    except Exception as e:
        logging.error(f"Error procesando pago: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()

if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)
