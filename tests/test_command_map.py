from matter_mcp import command_map as cm


def test_read_command_onoff():
    assert cm.read_command(1, 1, "OnOff", "OnOff") == "onoff read on-off 1 1"


def test_read_command_temperature():
    assert cm.read_command(2, 1, "TemperatureMeasurement", "MeasuredValue") == \
        "temperaturemeasurement read measured-value 2 1"


def test_read_command_unsupported_pair_returns_none():
    assert cm.read_command(1, 1, "OnOff", "GlobalSceneControl") is None
    assert cm.read_command(1, 1, "LevelControl", "CurrentLevel") is None


def test_invoke_command_on():
    assert cm.invoke_command(1, 1, "OnOff", "On") == "onoff on 1 1"


def test_invoke_command_off():
    assert cm.invoke_command(1, 1, "OnOff", "Off") == "onoff off 1 1"


def test_invoke_command_toggle():
    assert cm.invoke_command(1, 1, "OnOff", "Toggle") == "onoff toggle 1 1"


def test_invoke_command_unsupported_returns_none():
    assert cm.invoke_command(1, 1, "OnOff", "GlobalSceneControl") is None
    assert cm.invoke_command(1, 1, "LevelControl", "MoveToLevel") is None


def test_descriptor_parts_list_command():
    assert cm.parts_list_command(1) == "descriptor read parts-list 1 0"


def test_descriptor_server_list_command():
    assert cm.server_list_command(1, 1) == "descriptor read server-list 1 1"
