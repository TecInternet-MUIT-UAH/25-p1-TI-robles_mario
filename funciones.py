from pymongo import MongoClient
import requests
import re
import bcrypt
import json

'''
Escribir datos en Beebote
'''
def beebote_write(token, channel, resource, numero):
    headers = {
        "Content-Type": "application/json",
        'X-Auth-Token': token,
    }
    data = {
        "data": numero
    }
    response=requests.post(f"https://api.beebotte.com/v1/data/write/{channel}/{resource}",headers=headers,data=json.dumps(data))

'''
Leer datos de Beebotte
'''
def beebote_read(token, channel, resource):
    headers = {
        'X-Auth-Token': token,
    }
    url= f"https://api.beebotte.com/v1/data/read/{channel}/{resource}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza un error si la respuesta no es 200
        data = response.json()
        valores = [d["data"] for d in data if isinstance(d["data"], (int, float))]
        media=sum(valores) / len(valores) if valores else None
        return media
    except:
        return None

'''
Obtener un número aleatorio de la página web: https://www.numeroalazar.com.ar/
'''
def get_ramdom_number():
    response=requests.get('https://www.numeroalazar.com.ar/')
    if response.status_code==200:
        match=re.search(r'<div[^>]*id="numeros_generados"[^>]*>(.*?)</div>',response.text,re.DOTALL)
        numbers_aux=match.group(1)
        numbers=re.findall(r"\d+\.\d+",numbers_aux)
        numbers_valid=[n for n in numbers if re.match(r'^\d+\.\d+$',n)]
        if numbers_valid: 
            return int(float(numbers_valid[0]))
        return None
    else:
        print("Error al acceder a la pagina:",response.status_code)

'''
Generar y almacenar un número en la base de datos y Beebotte
'''
def number_request(data_base,token,channel,resource):
    numero = get_ramdom_number()
    data_base.numeros.insert_one({'numero': numero})
    beebote_write(token=token,channel=channel,resource=resource,numero=numero)
    return numero
    
