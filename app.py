from flask import Flask, request, jsonify
import sqlite3 as sq
from marshmallow import ValidationError
import bcrypt
import secrets
import datetime
from codicefiscale import codicefiscale

from utils.validate import validate
from models.Login import Login
from models.Dipendente import Dipendente
from models.Token import Token

app = Flask(__name__)

def get_db():
    conn = sq.connect('../CodiceFiscale.sqlite3')
    conn.row_factory = sq.Row
    return conn

@app.route('/', methods = ['GET'])
def hello():
    return 'Hello world!'

@app.route('/login', methods = ['POST'])
def login():
    try:
        result = validate(request.json, Login())
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    email = result["Email"]
    password = result["Password"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM TUser WHERE email = ? AND password = ?", [str(email), str(password)])
    account = cur.fetchone()

    if not email == account['email']:
        return jsonify({"message": "account non trovato"}), 404
    if not password == account['password']:
        return jsonify({"message": "password errata"}), 401

    token = secrets.token_hex(16)
    gap = datetime.timedelta(minutes=1) 
    dataNow = datetime.datetime.now() + gap
    cur.execute("UPDATE TUser SET token = ?, dataScadenzaToken = ? WHERE email = ?", [str(token), str(dataNow), str(email)])
    conn.commit()

    return jsonify({"email": email, "token": token}), 200

@app.route('/dipendente', methods = ['POST'])
def post_dipendente():
    try:
        result = validate(request.json, Dipendente())
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    token = result['Token']
    if not tokenIsValid(token):
        return jsonify({ "message": "Token non valido o scaduto" }), 401
    
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT codiceCatastale FROM TCodiciCatastali WHERE comune = ?", [str(result['Comune']).upper()])
    try:
        codCatastale = cur.fetchone()["codiceCatastale"]
    except:
        return jsonify({"message": "Comune non esistente"}), 400
    
    cur.execute("INSERT INTO TDipendenti (nome, cognome, nascita, sesso, codiceComune) VALUES (?, ?, ?, ?, ?)", [result['Nome'], result['Cognome'], result['Nascita'], result['Sesso'], codCatastale])
    conn.commit()

    return jsonify({"Nome": result['Nome'], "Cognome": result["Cognome"], "Nascita": result['Nascita'], "Sesso": result['Sesso'], "Codice catastale": codCatastale}), 201

@app.route('/dipendente', methods = ['GET'])
def get_dipendente():
    try:
        token = validate(request.json, Token())['Token'] 
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    if not tokenIsValid(token):
        return jsonify({ "message": "Token non valido o scaduto" }), 401

    query = request.args.get('nome')

    conn = get_db()
    cur = conn.cursor()

    if query:
        cur.execute("SELECT * FROM TDipendenti WHERE Nome LIKE ? OR Cognome LIKE ?", ["%"+query+"%", "%"+query+"%"])
        data = cur.fetchall()
    else: 
        cur.execute("SELECT * FROM TDipendenti")
        data = cur.fetchall()

    aus = []
    for x in data:
        aus.append({
            "id": x[0],
            "Nome": x[1], 
            "Cognome": x[2], 
            "Nascita": x[3], 
            "Sesso": x[4], 
            "Codice catastale": x[5]
        })

    return jsonify(aus)

@app.route('/dipendente/<int:id>', methods = ['DELETE'])
def del_dipendente(id):
    try:
        token = validate(request.json, Token())['Token'] 
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    if not tokenIsValid(token):
        return jsonify({ "message": "Token non valido o scaduto" }), 401

    cur.execute("SELECT * FROM TDipendenti WHERE id = ?", [str(id)])
    data = cur.fetchone()

    if not data:
        return jsonify({ "message": "Dipendente non trovato" }), 404

    cur.execute("DELETE FROM TDipendenti WHERE id = ?", [str(id)])
    conn.commit()

    return jsonify({ "message": "Dipendente eliminato" }), 201

@app.route('/dipendente/<int:id>', methods = ['PATCH'])
def patch_dipendente(id):
    try:
        result = validate(request.json, Dipendente())
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    token = result['Token']
    if not tokenIsValid(token):
        return jsonify({ "message": "Token non valido o scaduto" }), 401
    
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM TDipendenti WHERE id = ?", [str(id)])
    data = cur.fetchone()

    if not data:
        return jsonify({ "message": "Dipendente non trovato" }), 404
    
    cur.execute("SELECT codiceCatastale FROM TCodiciCatastali WHERE comune = ?", [str(result['Comune']).upper()])
    try:
        codCatastale = cur.fetchone()["codiceCatastale"]
    except:
        return jsonify({"message": "Comune non esistente"}), 400
    
    cur.execute("UPDATE TDipendenti SET nome = ?, cognome = ?, nascita = ?, sesso = ?, codiceComune = ?", [result['Nome'], result['Cognome'], result['Nascita'], result['Sesso'], codCatastale])
    conn.commit()

    return jsonify({"Nome": result['Nome'], "Cognome": result["Cognome"], "Nascita": result['Nascita'], "Sesso": result['Sesso'], "Codice catastale": codCatastale}), 201


@app.route("/calcolo", methods = ['GET'])
def calcolo():
    try:
        token = validate(request.json, Token())['Token'] 
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    if not tokenIsValid(token):
        return jsonify({ "message": "Token non valido o scaduto" }), 401
    
    cur.execute("SELECT * FROM TDipendenti")
    data = cur.fetchall()

    for x in data:
        aus = str(x[3]).split("-")
        aus = str(aus[1] + "/" + aus[2] + "/" + aus[0])
        cf = codicefiscale.encode(
            firstname=x[1],
            lastname=x[2],
            gender=x[4],
            birthdate=aus,
            birthplace=x[5],
        )

        cur.execute("UPDATE TDipendenti SET codiceFiscale = ? WHERE id = ?", [str(cf), str(x[0])])
        conn.commit()

    return jsonify({"messagge": "successo"}), 201


def tokenIsValid(token):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT dataScadenzaToken FROM TUser WHERE token = ?", [str(token)])
    data = cur.fetchone()
    if not data:
        return False
    
    dataExpire = datetime.datetime.strptime(data['dataScadenzaToken'], '%Y-%m-%d %H:%M:%S.%f')

    dataNow = datetime.datetime.now()
    
    if dataExpire > dataNow:
        return True
    return False
