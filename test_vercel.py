from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Minimal Flask works on Vercel!'})

@app.route('/')
def index():
    return jsonify({'message': 'Root endpoint works!'})
