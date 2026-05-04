import json, math

def haversine(lat1, lon1, lat2, lon2):
    
    # distance between latitudes
    # and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0

    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) + pow(math.sin(dLon / 2), 2) * math.cos(lat1) * math.cos(lat2))
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c

f = open("road_data.json", encoding='UTF-8')

data = json.load(f)

graph = {"edges":[], "nodes":[], "crew_costs":[], "budget":0}

graph["crew_costs"] = [6, 8, 7, 10, 9, 11]
graph["budget"] = 400

weights = {
    "unclassified":1, 
    "living_street":2, 
    "residential":2, 
    "tertiary":4, 
    "secondary":8,
    "primary":16,
    "trunk":32,
    "motorway":64,
    "tertiary_link":3,
    "secondary_link":6,
    "primary_link":12,
    "trunk_link":25,
    "motorway_link":51
    }

for road in data["elements"]:
    for node, geom in zip(road["nodes"], road["geometry"]):
        graph["nodes"].append({"id": node, "position":geom})
    for i in range(len(road["nodes"])-1):
        start_node = road["nodes"][i]
        end_node = road["nodes"][i+1]
        start_lat, start_lon = road["geometry"][i]["lat"], road["geometry"][i]["lon"]
        end_lat, end_lon = road["geometry"][i+1]["lat"], road["geometry"][i+1]["lon"]
        distance = haversine(start_lat, start_lon, end_lat, end_lon)
        if "lanes" in road["tags"]:
            lanes = int(road["tags"]["lanes"])
        else:
            lanes = 2
        graph["edges"].append(
            {
                "id":f"{road["id"]}-{i}",
                "base_time":math.ceil(distance*lanes*1000),
                "load":weights[road["tags"]["highway"]] if "highway" in road["tags"] else 1,
                "start":start_node,
                "end":end_node
                }
        )

result = open("parsing_results.json", "x")
json.dump(graph, result, indent=1)