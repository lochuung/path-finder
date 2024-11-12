import json

# Load the building.json data
with open("building.json") as f:
    building_data = json.load(f)

# Initialize the output format
building_nodes = []

# Transform each building into the desired format
for building_id, building_info in building_data.items():
    building_entry = {
        "name": building_info["properties"]["tags"].get("name", "Unknown"),
        "cords": building_info["geometry"]["coordinates"][0]
    }
    building_nodes.append(building_entry)

# Print or save the result as needed
print(json.dumps({"building_nodes": building_nodes}, indent=4, ensure_ascii=False))

