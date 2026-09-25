from copy import deepcopy
from threading import RLock
from uuid import uuid4
from flask import Flask, jsonify, request

app = Flask(__name__)
LOCK = RLock()

class SnapshotStore:
    def __init__(self):
        self.state = {}
        self.version = 0
        self.checkpoints = {}

    def update(self, key, value):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        key = key.strip()
        if len(key) > 128:
            raise ValueError("key must be 1-128 characters")
        self.version += 1
        self.state[key] = value
        return {"key": key, "value": value, "version": self.version}

    def create_checkpoint(self, name=None):
        checkpoint_id = uuid4().hex[:12]
        if name is not None:
            name = str(name).strip()
            if len(name) > 100:
                raise ValueError("name must be at most 100 characters")
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "name": name or checkpoint_id,
            "version": self.version,
            "state": deepcopy(self.state),
        }
        self.checkpoints[checkpoint_id] = checkpoint
        return deepcopy(checkpoint)

    def restore(self, checkpoint_id):
        if checkpoint_id not in self.checkpoints:
            raise KeyError("checkpoint not found")
        checkpoint = self.checkpoints[checkpoint_id]
        self.state = deepcopy(checkpoint["state"])
        self.version += 1
        return {
            "checkpoint_id": checkpoint_id,
            "restored_version": checkpoint["version"],
            "current_version": self.version,
            "state": deepcopy(self.state),
        }

    def get_checkpoint(self, checkpoint_id):
        if checkpoint_id not in self.checkpoints:
            raise KeyError("checkpoint not found")
        return deepcopy(self.checkpoints[checkpoint_id])

    def delete_checkpoint(self, checkpoint_id):
        return self.checkpoints.pop(checkpoint_id, None) is not None

    def stats(self):
        return {
            "version": self.version,
            "keys": len(self.state),
            "checkpoints": len(self.checkpoints),
        }

store=SnapshotStore()

@app.get("/health")
def health():
    with LOCK:
        return jsonify({"status":"ok","version":store.version,"checkpoints":len(store.checkpoints)})

@app.put("/api/state")
def update_state():
    body=request.get_json(silent=True) or {}
    if "value" not in body:
        return jsonify({"error":"value is required"}),400
    try:
        with LOCK:
            return jsonify(store.update(body.get("key"),body["value"]))
    except ValueError as exc:
        return jsonify({"error":str(exc)}),400

@app.get("/api/state")
def get_state():
    with LOCK:
        return jsonify({"version":store.version,"state":deepcopy(store.state)})

@app.post("/api/checkpoints")
def create_checkpoint():
    body=request.get_json(silent=True) or {}
    try:
        with LOCK:
            return jsonify(store.create_checkpoint(body.get("name"))),201
    except ValueError as exc:
        return jsonify({"error":str(exc)}),400

@app.get("/api/checkpoints")
def list_checkpoints():
    with LOCK:
        items=[{"checkpoint_id":c["checkpoint_id"],"name":c["name"],
                "version":c["version"],"keys":len(c["state"])}
               for c in store.checkpoints.values()]
    return jsonify({"checkpoints":items,"count":len(items)})

@app.get("/api/checkpoints/<checkpoint_id>")
def get_checkpoint(checkpoint_id):
    with LOCK:
        try:
            return jsonify(store.get_checkpoint(checkpoint_id))
        except KeyError:
            return jsonify({"error":"checkpoint not found"}),404

@app.post("/api/checkpoints/<checkpoint_id>/restore")
def restore_checkpoint(checkpoint_id):
    with LOCK:
        try:
            return jsonify(store.restore(checkpoint_id))
        except KeyError:
            return jsonify({"error":"checkpoint not found"}),404

@app.delete("/api/checkpoints/<checkpoint_id>")
def delete_checkpoint(checkpoint_id):
    with LOCK:
        if not store.delete_checkpoint(checkpoint_id):
            return jsonify({"error":"checkpoint not found"}),404
    return jsonify({"checkpoint_id":checkpoint_id,"deleted":True})

@app.get("/api/stats")
def stats():
    with LOCK:
        return jsonify(store.stats())

if __name__=="__main__":
    app.run(debug=True)
