from flask import Flask, jsonify

app = Flask(__name__, static_folder='static')

@app.route('/api/hello')
def hello():
    return jsonify(message="¡Hola desde Flask!")

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
