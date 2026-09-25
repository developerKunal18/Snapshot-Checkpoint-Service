import pytest
import app as module

@pytest.fixture(autouse=True)
def reset_store():
    module.store=module.SnapshotStore()
    yield

@pytest.fixture
def client():
    module.app.config["TESTING"]=True
    return module.app.test_client()

def test_health(client):
    r=client.get("/health")
    assert r.status_code==200
    assert r.get_json()["status"]=="ok"

def test_checkpoint_captures_state(client):
    client.put("/api/state",json={"key":"status","value":"online"})
    r=client.post("/api/checkpoints",json={"name":"safe"})
    assert r.status_code==201
    c=r.get_json()
    assert c["name"]=="safe"
    assert c["version"]==1
    assert c["state"]=={"status":"online"}

def test_restore_checkpoint(client):
    client.put("/api/state",json={"key":"status","value":"online"})
    c=client.post("/api/checkpoints").get_json()
    client.put("/api/state",json={"key":"status","value":"maintenance"})
    r=client.post(f"/api/checkpoints/{c['checkpoint_id']}/restore")
    assert r.status_code==200
    assert r.get_json()["state"]=={"status":"online"}
    assert client.get("/api/state").get_json()["state"]=={"status":"online"}

def test_checkpoint_is_immutable(client):
    client.put("/api/state",json={"key":"count","value":1})
    c=client.post("/api/checkpoints").get_json()
    client.put("/api/state",json={"key":"count","value":2})
    client.post(f"/api/checkpoints/{c['checkpoint_id']}/restore")
    saved=client.get(f"/api/checkpoints/{c['checkpoint_id']}").get_json()
    assert saved["state"]["count"]==1

def test_missing_checkpoint(client):
    assert client.post("/api/checkpoints/missing/restore").status_code==404

def test_delete_checkpoint(client):
    c=client.post("/api/checkpoints").get_json()
    cid=c["checkpoint_id"]
    assert client.delete(f"/api/checkpoints/{cid}").status_code==200
    assert client.get(f"/api/checkpoints/{cid}").status_code==404
