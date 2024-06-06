from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from firebase_admin import credentials, initialize_app, firestore
import random

app = Flask(__name__)

# Inicialização do Firebase
cred = credentials.Certificate('./mobilegs-e7127-firebase-adminsdk-bfgiy-bf191a87d5.json')
initialize_app(cred)
db = firestore.client()

# Configurações do email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ntjntjntjntj1@gmail.com'  # Coloque seu email do Gmail
app.config['MAIL_PASSWORD'] = 'vpti ctyk nbha lazw'  # Coloque a senha do seu email do Gmail
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email).where('senha', '==', senha)
    snapshot = query.get()

    if len(snapshot) == 1:
        user_data = snapshot[0].to_dict()
        return jsonify({"success": True, "user": user_data}), 200
    else:
        return jsonify({"success": False, "message": "Email ou senha inválidos."}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) > 0:
        return jsonify({"success": False, "message": "Email já cadastrado."}), 400
    id = random.randint(100000, 999999)  # Exemplo de geração automática de ID
    new_user_ref = db.collection('usuarios').document(str(id))
    new_user_ref.set({
        'id': id,
        'email': email,
        'senha': senha,
        'token_recuperacao': ''
    })

    return jsonify({"success": True, "message": "Usuário registrado com sucesso.", "id": id}), 200

# Rota para recuperar a senha
@app.route('/recuperar_senha', methods=['POST'])
def recuperar_senha():
    data = request.get_json()
    email = data.get('email')

    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) == 0:
        return jsonify({"success": False, "message": "Email não encontrado."}), 404

    token_recuperacao = 'abc123'

    for doc in snapshot:
        doc.reference.update({"token_recuperacao": token_recuperacao})
    
    print(f"Token de recuperação gerado para email {email}: {token_recuperacao}")

    msg = Message('Recuperação de Senha', sender='seu_email@gmail.com', recipients=[email])
    msg.body = f'Olá,\n\nVocê solicitou a recuperação de senha. Use o seguinte token para redefinir sua senha: {token_recuperacao}\n\nAtenciosamente,\nSua Aplicação'

    try:
        mail.send(msg)
        print(f"E-mail de recuperação enviado para {email}.")
        return jsonify({"success": True, "message": "Token de recuperação enviado para o seu email."}), 200
    except Exception as e:
        print(f"Erro ao enviar e-mail de recuperação para {email}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route('/redefinir_senha', methods=['POST'])
def redefinir_senha():
    # Receba os dados do formulário (email, token e nova senha)
    email = request.json.get('email')
    token = request.json.get('token')
    nova_senha = request.json.get('nova_senha')

    # Verifique se o email fornecido corresponde a um usuário
    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) == 0:
        return jsonify({"success": False, "message": "Email não encontrado."}), 404

    # Verificar se o token recebido é válido para o usuário
    for doc in snapshot:
        user_data = doc.to_dict()
        if user_data.get('token_recuperacao') == token:
            # Atualizar a senha do usuário no Firestore
            doc.reference.update({"senha": nova_senha})
            print('Senha redefinida com sucesso para o usuário com email:', email)
            return jsonify({"success": True, "message": "Senha redefinida com sucesso."}), 200
        else:
            return jsonify({"success": False, "error": "Token de redefinição de senha inválido."}), 400
        
@app.route('/reportar_localizacao', methods=['POST'])
def reportar_localizacao():
    try:
        data = request.get_json()

        if 'latitude' not in data or 'longitude' not in data:
            raise ValueError("Dados de localização incompletos.")

        latitude = data['latitude']
        longitude = data['longitude']

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordenadas inválidas.")

        location_ref = db.collection('localização').document()
        location_ref.set({
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': firestore.SERVER_TIMESTAMP 
        })

        return jsonify({"success": True, "message": "Localização salva com sucesso."}), 200

    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": "Erro interno do servidor."}), 500
    
 #################################################CRUD#############################################
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) > 0:
        return jsonify({"success": False, "message": "Email já cadastrado."}), 400

    new_user_ref = db.collection('usuarios').document(email)
    new_user_ref.set({
        'email': email,
        'senha': senha,
        'token_recuperacao': ''
    })

    return jsonify({"success": True, "message": "Usuário registrado com sucesso.", "email": email}), 200
##Listar
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    users_ref = db.collection('usuarios')
    users = []
    for doc in users_ref.stream():
        users.append(doc.to_dict())
    return jsonify({"success": True, "usuarios": users}), 200

##obter por email
@app.route('/usuarios/<email>', methods=['GET'])
def obter_usuario(email):
    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    for user in snapshot:
        return jsonify({"success": True, "usuario": user.to_dict()}), 200

    return jsonify({"success": False, "message": "Usuário não encontrado."}), 404
##Update do usario 
@app.route('/usuarios/<email>', methods=['PUT'])
def atualizar_usuario(email):
    data = request.get_json()
    nova_senha = data.get('nova_senha')

    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) == 0:
        return jsonify({"success": False, "message": "Usuário não encontrado."}), 404
    elif len(snapshot) > 1:
        return jsonify({"success": False, "message": "Mais de um usuário encontrado com o mesmo e-mail."}), 500

    user_ref = snapshot[0].reference
    user_ref.update({
        'senha': nova_senha,
    })

    return jsonify({"success": True, "message": "Usuário atualizado com sucesso."}), 200

#delete usuario
@app.route('/usuarios/<email>', methods=['DELETE'])
def excluir_usuario(email):
    users_ref = db.collection('usuarios')
    query = users_ref.where('email', '==', email)
    snapshot = query.get()

    if len(snapshot) == 0:
        return jsonify({"success": False, "message": "Usuário não encontrado."}), 404
    elif len(snapshot) > 1:
        return jsonify({"success": False, "message": "Mais de um usuário encontrado com o mesmo e-mail."}), 500

    user_ref = snapshot[0].reference
    user_ref.delete()
    
    return jsonify({"success": True, "message": "Usuário excluído com sucesso."}), 200





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
