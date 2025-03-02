from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/admin/status', methods=['GET'])
def admin_status():
    return jsonify({"status": "Admin Node Running", "role": "HuobzEdge Admin"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5051)
