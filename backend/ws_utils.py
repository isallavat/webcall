import json
from datetime import datetime
from db_utils import execute_query


def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()

class WSIniter ():
    def __init__(self, conn):
        self.__conn = conn
        self.__collection = {}
        self.__events = []

    
    def init_user(self, user, ws):
        self.__collection[user['id']] = ws

        self.on(user['id'], 'call:join', lambda data: self.__handle_call_join(user, data))
        self.on(user['id'], 'call:leave', lambda data: self.__handle_call_left(user, data))
        self.on(user['id'], 'call:pc-offer', lambda data: self.__handle_pc_offer(user, data))
        self.on(user['id'], 'call:pc-answer', lambda data: self.__handle_pc_answer(user, data))
        self.on(user['id'], 'call:pc-ice-candidate', lambda data: self.__handle_pc_ice_candidate(user, data))
        self.on(user['id'], 'call:message', lambda data: self.__handle_chat_message(user, data))
        self.on(user['id'], 'call:messages', lambda data: self.__handle_get_chat_message(user, data))

        while not ws.closed:
            message = ws.receive()
            if message is None:
                return self.__handle_close(user)
            
            args = json.loads(message)
            event = args[0]

            for item in self.__events:
                if item['name'] == event and item['id'] == user['id']:
                    item['handler'](args[1])
        else:
            self.__handle_close(user)

    
    def on(self, user_id, event: str, handler):
        event_exists = False

        for item in self.__events:
            if item['id'] == user_id and item['name'] == event and id(handler) == id(item['handler']):
                event_exists = True

        if not event_exists:
            self.__events.append({ 'id': user_id, 'name': event, 'handler': handler })


    def send_to(self, user_id: str, event: str, data: object):
        ids = user_id if isinstance(user_id, list) else [user_id]
        message = json.dumps([event, data], default=datetime_serializer)

        for _id in ids:
            if self.__collection[_id]:
                self.__collection[_id].send(message)


    def __handle_close(self, user):
        del self.__collection[user['id']]
        self.__events = list(filter(lambda x: x['id'] != user['id'], self.__events))

        query = "UPDATE calls SET users = ARRAY_REMOVE(users, %s) WHERE %s = ANY(users) RETURNING *"
        result = execute_query(self.__conn, query, [user['id'], user['id']])
        
        for call in result:
            self.send_to(call['users'], 'call:user-disconnected', {'id': call['id'], 'user': user})
    

    def __handle_call_join(self, user, data):
        query = "UPDATE calls SET users = ARRAY_APPEND(users, %s) WHERE id=%s RETURNING *"
        call = execute_query(self.__conn, query, [user['id'], data['id']], 1)

        query = "SELECT id, name FROM users WHERE id = ANY(%s::UUID[])"
        users = execute_query(self.__conn, query, [call['users']])

        to = list(filter(lambda x: x != user['id'], call['users']))

        self.send_to(to, 'call:user-joined', {'id': data['id'], 'user': user})
        self.send_to(user['id'], 'call:joined', {'id': data['id'], 'users': users})
    

    def __handle_call_left(self, user, data):
        query = "UPDATE calls SET users = ARRAY_REMOVE(users, %s) WHERE id=%s RETURNING *"
        call = execute_query(self.__conn, query, [user['id'], data['id']], 1)

        to = list(filter(lambda x: x != user['id'], call['users']))

        self.send_to(to, 'call:user-left', {'id': data['id'], 'user': user})


    def __handle_pc_offer(self, user, data):
        query = "SELECT * FROM calls WHERE id=%s"
        call = execute_query(self.__conn, query, [data['id']], 1)
        
        to = data.get('to_user_id') or list(filter(lambda x: x != user['id'], call['users']))

        self.send_to(to, 'call:pc-offer', {**data, 'user': user})

    
    def __handle_pc_answer(self, user, data):
        self.send_to(data['to_user_id'], 'call:pc-answer', {**data, 'user': user})


    def __handle_pc_ice_candidate(self, user, data):
        query = "SELECT * FROM calls WHERE id=%s"
        call = execute_query(self.__conn, query, [data['id']], 1)

        to = list(filter(lambda x: x != user['id'], call['users']))
        
        self.send_to(to, 'call:pc-ice-candidate', {**data, 'user': user})


    def __handle_chat_message(self, user, data):
        query = "INSERT INTO messages (text, user_id, call_id) VALUES (%s, %s, %s) RETURNING *"
        message = execute_query(self.__conn, query, [data['text'], user['id'], data['id']], 1)

        query = "SELECT * FROM calls WHERE id=%s"
        call = execute_query(self.__conn, query, [data['id']], 1)
        
        self.send_to(call['users'], 'call:message', {'id': data['id'], 'message': {**message, 'user_name': user['name']}})


    def __handle_get_chat_message(self, user, data):
        query = "SELECT messages.*, users.name as user_name FROM messages JOIN users ON messages.user_id = users.id WHERE messages.call_id=%s ORDER BY messages.created_at"
        messages = execute_query(self.__conn, query, [data['id']])
        
        self.send_to(user['id'], 'call:messages', {'id': data['id'], 'messages': messages})