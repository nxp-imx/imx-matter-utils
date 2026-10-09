from pathlib import Path

from matter_mcp.registry import Registry

# Resolve config/device_registry.json relative to the repo root.
# tests/ -> repo root -> config/device_registry.json
REGISTRY_PATH = str(Path(__file__).resolve().parent.parent / "config" / "device_registry.json")


def _load() -> Registry:
    return Registry.load(REGISTRY_PATH)


def test_load_yields_one_node():
    reg = _load()
    nodes = reg.list_nodes()
    assert len(nodes) == 1


def test_list_nodes_compact_shape():
    reg = _load()
    nodes = reg.list_nodes()
    node1 = next(n for n in nodes if n["node_id"] == 1)
    assert node1["node_id"] == 1
    assert node1["label"] == "lab_light"
    assert node1["type"] == "light"
    # endpoints must be a list of ints, not full cluster objects
    assert node1["endpoints"] == [1]


def test_get_node_full_layers():
    reg = _load()
    node = reg.get_node(1)
    assert node is not None
    # Annotation layer
    assert node["label"] == "lab_light"
    assert node["type"] == "light"
    assert node["room"] == "lab"
    # Identity layer
    assert node["node_id"] == 1
    assert node["commissioned"] is True
    # Discovery layer
    assert node["discovery"] == {"source": "manual"}
    # Endpoints with full cluster names and device_type
    assert node["endpoints"] == [
        {"endpoint": 1, "device_type": "DimmableLight", "clusters": ["OnOff", "LevelControl"]}
    ]


def test_get_node_missing_returns_none():
    reg = _load()
    assert reg.get_node(999) is None


def test_has_endpoint():
    reg = _load()
    assert reg.has_endpoint(1, 1) is True
    assert reg.has_endpoint(1, 2) is False
    assert reg.has_endpoint(999, 1) is False


def test_endpoint_has_cluster():
    reg = _load()
    assert reg.endpoint_has_cluster(1, 1, "OnOff") is True
    assert reg.endpoint_has_cluster(1, 1, "TemperatureMeasurement") is False
    assert reg.endpoint_has_cluster(1, 1, "LevelControl") is True
    assert reg.endpoint_has_cluster(999, 1, "OnOff") is False


def test_iter_nodes_returns_full_nodes():
    reg = _load()
    nodes = reg.iter_nodes()
    assert len(nodes) == 1
    assert nodes[0]["node_id"] == 1
    assert "endpoints" in nodes[0] and "discovery" in nodes[0]
