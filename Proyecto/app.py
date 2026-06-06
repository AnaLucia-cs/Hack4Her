import os
from flask import Flask, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__, static_folder='static')

mongodb_uri = os.getenv('MONGODB_URI') or os.getenv('MONGODB_ATLAS_URI')
mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000) if mongodb_uri else None
mongo_db = mongo_client[os.getenv('MONGODB_DB')] if mongo_client and os.getenv('MONGODB_DB') else None

@app.route('/api/hello')
def hello():
    return jsonify(message="¡Hola desde Flask!")

@app.route('/')
def index():
  return render_template("home.html")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
