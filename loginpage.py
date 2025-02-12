from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from funciones import *
import requests
import re
import bcrypt
import json

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'

client = MongoClient('mongodb://localhost:27017/')
db = client.mi_base_de_datos 

token=""
channel="Numeros_aleatorios"
resource="numeros"
numero_ultimo=""

"""
Página web de entrada a la aplicación
"""
@app.route('/')
def inicio():
    global numero_ultimo  
    if 'usuario' in session:
        ultimo_numero_doc = db.numeros.find_one(
            {}, sort=[("_id", -1)]
        )
        numero_ultimo = ultimo_numero_doc["numero"] if ultimo_numero_doc else "No tiene números registrados"
        return render_template('inicio.html', numero=numero_ultimo, media_result="")
    else:
        session["numero_no_registrado"] = number_request(data_base=db,token=token,channel=channel,resource=resource)
        return render_template('inicio.html', numero=session["numero_no_registrado"], media_result="")


"""
Generación de número y actualización
"""
@app.route('/solicitar_numero', methods=['POST'])
def solicitar_numero():
    global numero_ultimo  
    numero_ultimo=number_request(data_base=db,token=token,channel=channel,resource=resource)    
    return render_template('inicio.html', numero=numero_ultimo, media_result="")

'''
Cálculo de la media (base de datos local)
'''
@app.route('/media_local', methods=['POST'])
def media_local():
    global numero_ultimo  
    numeros_registrados = [doc["numero"] for doc in db.numeros.find()]
    media = sum(numeros_registrados) / len(numeros_registrados) if numeros_registrados else 0

    usuario = session["usuario"]
    solicitud = db.media_solicitudes.find_one({"usuario": usuario})
    if solicitud:
        db.media_solicitudes.update_one({"usuario": usuario}, {"$inc": {"conteo": 1}})
        conteo = solicitud["conteo"] + 1
    else:
        db.media_solicitudes.insert_one({"usuario": usuario, "conteo": 1})
        conteo = 1

    if numeros_registrados:
        return render_template('inicio.html', numero=numero_ultimo, media_result=f"Media local: {media:.2f} (Solicitada {conteo} veces)")
    else:
        return render_template('inicio.html', numero=numero_ultimo, media_result="No hay números para calcular la media")


'''
Cálculo de la media (base de datos externa en Beebotte)
'''
@app.route('/media_internet', methods=['POST'])
def media_internet():
    global numero_ultimo  
    media=beebote_read(token=token,channel=channel,resource=resource)
    usuario = session["usuario"]
    solicitud = db.media_solicitudes_online.find_one({"usuario": usuario})
    if solicitud:
        db.media_solicitudes_online.update_one({"usuario": usuario}, {"$inc": {"conteo": 1}})
        conteo = solicitud["conteo"] + 1
    else:
        db.media_solicitudes_online.insert_one({"usuario": usuario, "conteo": 1})
        conteo = 1
    # Renderizamos la plantilla con los valores correctos
    if media is not None:
        return render_template(
            'inicio.html',
            numero=numero_ultimo,  # Asegúrate de que esta variable esté definida correctamente
            media_result=f"Media local: {media:.2f} (Solicitada {conteo} veces)"
        )
    else:
        return render_template(
            'inicio.html',
            numero=numero_ultimo,
            media_result="No hay números para calcular la media"
        )

'''
Visualización de la interfáz gráfica de Beebotte
'''
@app.route('/graficas_externas')
def graficas_externas():
    return render_template('graficas_externas.html')

'''
Autenticación de usuario (inicio de sesión)
'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        # Buscar el usuario en la base de datos
        user_data = db.usuarios.find_one({'usuario': usuario})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            # Si el usuario existe y la contraseña es correcta
            session['usuario'] = usuario
            return redirect(url_for('inicio'))
        else:
            # Si las credenciales no coinciden
            return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')

'''
Visualizar perfil de usuario
'''
@app.route('/profile')
def perfil():
    return render_template('profile.html')
   

'''
Formulario de registro de usuario
'''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']  
        usuario = request.form['usuario']
        password = request.form['password']

        
        if db.usuarios.find_one({'usuario': usuario}):
            return "El nombre de usuario ya está registrado", 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        db.usuarios.insert_one({
            'email': email,  
            'usuario': usuario,
            'password': hashed_password
        })

        return redirect(url_for('login'))

    return render_template('register.html')


'''
Finalizar sesión del usuario
'''
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('inicio'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

