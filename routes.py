from flask import Blueprint, jsonify, request, render_template

bp = Blueprint('routes', __name__)
server_instance = None

def init_app(app, server):
    global server_instance
    server_instance = server
    app.register_blueprint(bp)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/messages')
def get_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    if user1 and user2:
        return jsonify(server_instance.get_messages_between(user1, user2))
    return jsonify(server_instance.messages)

@bp.route('/conversations')
def get_conversations():
    conversations = server_instance.get_conversations()
    return jsonify([f"{p[0]} <--> {p[1]}" for p in conversations.keys()])
