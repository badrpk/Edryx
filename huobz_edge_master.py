import requests
import json

# List of registered devices
edge_devices = [
    "http://192.168.1.100:5000",  # Example IPs of edge devices
    "http://192.168.1.101:5000",
    "http://192.168.1.102:5000"
]

def distribute_task(task_type, data):
    """Sends a processing task to all available edge devices"""
    for device in edge_devices:
        try:
            response = requests.post(f"{device}/process", json={"task_type": task_type, "data": data})
            if response.status_code == 200:
                print(f"✅ Task Completed by {device}: {response.json()['result']}")
            else:
                print(f"⚠️ Failed on {device}")
        except Exception as e:
            print(f"❌ Error connecting to {device}: {e}")

# Example: Assign AI Training to Edge Nodes
task_data = {"dataset": "huobz_training_data.json"}
distribute_task("AI Training", task_data)
