# Real chip-tool interactive server WebSocket JSON samples (recorded from a local chip-lighting-app node 1)
# Recording date: see git history. lighting-app: discriminator 3840, passcode 20202021. Commissioned via onnetwork, node_id=1.

## onoff read on-off 1 1 (light is off) -> successful bool read
{"results":[{"attributeId":0,"clusterId":6,"dataVersion":2968225,"endpointId":1,"value":false}],"logs":[...base64...]}

## onoff on 1 1 -> successful command (empty results array)
{"results":[],"logs":[...]}

## descriptor read parts-list 1 0 -> endpoint list
{"results":[{"attributeId":3,"clusterId":29,"endpointId":0,"value":[1]}]}

## descriptor read server-list 1 1 -> list of numeric cluster IDs
{"results":[{"attributeId":1,"clusterId":29,"endpointId":1,"value":[29,4,3,6,8,768]}]}

## temperaturemeasurement read measured-value 1 1 (light has no temperature cluster) -> failure
{"results":[{"attributeId":0,"clusterId":1026,"endpointId":1,"error":"UNSUPPORTED_CLUSTER"},{"error":"FAILURE"}]}

## onoff read on-off 1 99 (endpoint does not exist) -> failure
{"results":[{"attributeId":0,"clusterId":6,"endpointId":99,"error":"UNSUPPORTED_ENDPOINT"},{"error":"FAILURE"}]}

# Key contract:
# - Successful read: results[0].value = the natively parsed value (bool/int/list). Temperature is an integer in hundredths of a degree, divide by 100.
# - Successful command: results == [].
# - Failure: results[0] has "error":"<CODE>". CODE mapping: UNSUPPORTED_CLUSTER->unsupported_cluster, UNSUPPORTED_ENDPOINT->unknown_endpoint, anything else->generic error.
# - server-list value = array of numeric cluster IDs; look them up in cluster_map to write names back into discovery.
# - logs are all base64 debug logs; the parser ignores them.
