from matter_mcp import response_parser as rp


# --- parse_read ---

def test_parse_read_success_bool():
    resp = {"results": [{"attributeId": 0, "clusterId": 6, "dataVersion": 2968225,
                         "endpointId": 1, "value": False}], "logs": []}
    assert rp.parse_read(resp) == {"ok": True, "value": False}


def test_parse_read_success_int_value():
    resp = {"results": [{"attributeId": 0, "clusterId": 1026, "endpointId": 1,
                         "value": 2650}], "logs": []}
    assert rp.parse_read(resp) == {"ok": True, "value": 2650}


def test_parse_read_unsupported_cluster():
    resp = {"results": [{"attributeId": 0, "clusterId": 1026, "endpointId": 1,
                         "error": "UNSUPPORTED_CLUSTER"}, {"error": "FAILURE"}]}
    assert rp.parse_read(resp) == {"ok": False, "error": "unsupported_cluster"}


def test_parse_read_unsupported_endpoint():
    resp = {"results": [{"attributeId": 0, "clusterId": 6, "endpointId": 99,
                         "error": "UNSUPPORTED_ENDPOINT"}, {"error": "FAILURE"}]}
    assert rp.parse_read(resp) == {"ok": False, "error": "unknown_endpoint"}


def test_parse_read_unknown_error_maps_to_chip_error():
    resp = {"results": [{"error": "SOME_OTHER_FAILURE"}]}
    assert rp.parse_read(resp) == {"ok": False, "error": "chip_error"}


def test_parse_read_empty_results_is_chip_error():
    assert rp.parse_read({"results": []}) == {"ok": False, "error": "chip_error"}


def test_parse_read_missing_results_is_chip_error():
    assert rp.parse_read({}) == {"ok": False, "error": "chip_error"}


# --- parse_command ---

def test_parse_command_empty_results_is_success():
    resp = {"results": [], "logs": []}
    assert rp.parse_command(resp) == {"ok": True, "status": "SUCCESS"}


def test_parse_command_no_error_is_success():
    # some commands echo a result row without an error
    resp = {"results": [{"clusterId": 6, "endpointId": 1}], "logs": []}
    assert rp.parse_command(resp) == {"ok": True, "status": "SUCCESS"}


def test_parse_command_error_maps():
    resp = {"results": [{"error": "UNSUPPORTED_ENDPOINT"}, {"error": "FAILURE"}]}
    assert rp.parse_command(resp) == {"ok": False, "error": "unknown_endpoint"}


def test_parse_command_missing_results_is_chip_error():
    assert rp.parse_command({}) == {"ok": False, "error": "chip_error"}


# --- parse_descriptor_list ---

def test_parse_descriptor_list_parts():
    resp = {"results": [{"attributeId": 3, "clusterId": 29, "endpointId": 0,
                         "value": [1]}]}
    assert rp.parse_descriptor_list(resp) == [1]


def test_parse_descriptor_list_server_list():
    resp = {"results": [{"attributeId": 1, "clusterId": 29, "endpointId": 1,
                         "value": [29, 4, 3, 6, 8, 768]}]}
    assert rp.parse_descriptor_list(resp) == [29, 4, 3, 6, 8, 768]


def test_parse_descriptor_list_error_is_empty():
    resp = {"results": [{"error": "UNSUPPORTED_ENDPOINT"}]}
    assert rp.parse_descriptor_list(resp) == []


def test_parse_descriptor_list_missing_is_empty():
    assert rp.parse_descriptor_list({}) == []
