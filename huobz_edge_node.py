import os
import json
import torch
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Get device info
device_name = os.uname().nodename
device_type = "GPU" if torch.cuda.is_available() else "CPU"

# Storage check
total_memory = torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 0
available_memory = total_memory - torch.cuda.memory_reserved(0) if torch.cuda.is_available() else 0

@app.route("/register", methods=["POST"])
def register():
    """Registers the device to the HuobzEdge network"""
    data = request.json
    print(f"✅ Connected to {data['master_node']}")
    return jsonify({"message": f"{device_name} registered successfully!"})

@app.route("/process", methods=["POST"])
def process_task():
    """Receives and processes tasks"""
    task_data = request.json
    print(f"🖥️ Processing Task: {task_data['task_type']}")

    # Simulate processing
    result = f"Processed {task_data['task_type']} on {device_name}"

    return jsonify({"result": result, "device": device_name})

if __name__ == "__main__":
    print(f"🚀 {device_name} (Type: {device_type}) Ready on HuobzEdge")
    app.run(host="0.0.0.0", port=5050)
