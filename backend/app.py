import os
import logging
import psycopg2
import jwt
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from dotenv import load_dotenv
from db_utils import init_db, execute_query
from ws_utils import WSIniter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cwd = os.getcwd()
load_dotenv(os.path.join(cwd, '.env'))

conn = psycopg2.connect(os.getenv('DATABASE_URI'))

build_folder = os.path.join(cwd, 'dist')

app = Flask(__name__, template_folder=build_folder, static_folder=build_folder, static_url_path='/')
sockets = Sockets(app)
ws_initer = WSIniter(conn)
CORS(app)

def get_user_by_token(token):
    token = token.replace('Bearer ', '')
    query = "SELECT user_id FROM tokens WHERE token=%s"
    result = execute_query(conn, query, [token], 1)

    if not result:
        return False
    
    query = "SELECT * FROM users WHERE id=%s"
    return execute_query(conn, query, [result['user_id']], 1)


@app.route('/api/me', methods=['GET'])
def get_user():
    user = get_user_by_token(request.headers.get('Authorization', ''))
    
    if user:
        return user
    else:
        return {'error': 'User not found'}, 404


@app.route('/api/users', methods=['POST'])
def create_user():
    name = request.get_json().get('name')
    query = "INSERT INTO users (name) VALUES (%s) RETURNING id"
    result = execute_query(conn, query, [name], 1)
    token = jwt.encode({'id': result['id']}, 'secret', algorithm='HS256')

    query = "INSERT INTO tokens (user_id, token) VALUES (%s, %s) RETURNING *"
    result = execute_query(conn, query, [result['id'], token], 1)
    
    return {'token': result['token']}


@app.route('/api/calls', methods=['POST'])
def create_call():
    user = get_user_by_token(request.headers.get('Authorization', ''))

    if not user:
        return {'error': 'User not found'}, 404
    
    query = "INSERT INTO calls (users) VALUES (ARRAY[]::VARCHAR[]) RETURNING *"
    result = execute_query(conn, query, size=1)
    
    return result
    

@app.route('/')
def index():
    return render_template('index.html')


@sockets.route('/echo')
def echo_socket(ws):
    user = get_user_by_token(request.args.get('token'))

    if user:
        ws_initer.init_user(user, ws)
    else:
        ws.send('unauthorized')
        ws.close()


if __name__ == "__main__":
    try:
        init_db(conn)
        
        port = int(os.getenv('API_PORT', 80))
        
        logger.info("WSGIServer started on port %s", port)
        
        server = pywsgi.WSGIServer(('', port), app, handler_class=WebSocketHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server interrupted. Cleaning up...")
        # Perform any cleanup operations here if needed
    finally:
        print("Exiting the program.")
