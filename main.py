import threading
from flask import Flask
from server import Server
import routes

app = Flask(__name__, static_folder='static', template_folder='templates')
server = Server('0.0.0.0', 5555)

routes.init_app(app, server)

if __name__ == "__main__":
    threading.Thread(target=server.start_server).start()
    app.run(host='0.0.0.0', port=5000)
