from matter_mcp import cluster_map


def test_cluster_id_known():
    assert cluster_map.cluster_id("OnOff") == 6
    assert cluster_map.cluster_id("LevelControl") == 8
    assert cluster_map.cluster_id("TemperatureMeasurement") == 1026
    assert cluster_map.cluster_id("OccupancySensing") == 1030


def test_cluster_id_unknown():
    assert cluster_map.cluster_id("DoorLock") is None


def test_is_supported_cluster():
    assert cluster_map.is_supported_cluster("OnOff") is True
    assert cluster_map.is_supported_cluster("TemperatureMeasurement") is True
    assert cluster_map.is_supported_cluster("LevelControl") is False
    assert cluster_map.is_supported_cluster("OccupancySensing") is False
    assert cluster_map.is_supported_cluster("DoorLock") is False


def test_is_supported_attribute():
    assert cluster_map.is_supported_attribute("OnOff", "OnOff") is True
    assert cluster_map.is_supported_attribute("TemperatureMeasurement", "MeasuredValue") is True
    assert cluster_map.is_supported_attribute("OnOff", "MeasuredValue") is False
    assert cluster_map.is_supported_attribute("LevelControl", "CurrentLevel") is False


def test_is_supported_command():
    assert cluster_map.is_supported_command("OnOff", "On") is True
    assert cluster_map.is_supported_command("OnOff", "Off") is True
    assert cluster_map.is_supported_command("OnOff", "Toggle") is True
    assert cluster_map.is_supported_command("LevelControl", "MoveToLevel") is False
