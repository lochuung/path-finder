import json
import math

from scipy.spatial import KDTree

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from simpleai.search import SearchProblem, astar


def haversine(lat1, lon1, lat2, lon2):
    # Haversine formula to calculate distance between two points
    R = 6371  # Radius of the Earth in km
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (pow(math.sin(dlat / 2), 2) +
         math.cos(lat1) * math.cos(lat2) * pow(math.sin(dlon / 2), 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


class Map:
    def __init__(self):
        self.graph = {}
        self.tree = None
        self.coordinates = []
        self.nodes = []
        self.loadMapData()

    def showMap(self, nodes, coordinates, path=None):
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd

        # Your Mapbox access token
        mapbox_token = "pk.eyJ1IjoibG9jaHV1bmciLCJhIjoiY20zY2RqdmN0MjB5MDJqb2wxb3lhMnc2biJ9.E39GAN-RK5he-1HAYFIZUA"

        px.set_mapbox_access_token(mapbox_token)

        # Prepare map data
        mapData = []
        for i in range(len(nodes)):
            mapData.append([nodes[i], coordinates[i][0], coordinates[i][1]])

        df = pd.DataFrame(mapData, columns=['id', 'lat', 'lon'])

        # Prepare edge data based on neighbors
        edge_lats = []
        edge_lons = []
        for node_id, node_info in self.graph.items():
            node_coord = self.getNodeCoordinateById(node_id)
            for neighbor_id in node_info['neighbors']:
                neighbor_coord = self.getNodeCoordinateById(neighbor_id)
                # Add edge from node to its neighbor
                edge_lats += [node_coord[1], neighbor_coord[1], None]
                edge_lons += [node_coord[0], neighbor_coord[0], None]

        # Create the figure
        fig = go.Figure()

        # Add edges as a Scattermapbox trace
        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=edge_lons,
                lat=edge_lats,
                line=dict(width=2, color='blue'),
                hoverinfo='none'
            )
        )

        # If a path is provided, highlight it on the map
        if path:
            path_lats = []
            path_lons = []
            for i in range(len(path) - 1):
                start_coord = self.getNodeCoordinateById(path[i])
                end_coord = self.getNodeCoordinateById(path[i + 1])
                path_lats += [start_coord[1], end_coord[1], None]
                path_lons += [start_coord[0], end_coord[0], None]

            # Add path as a separate Scattermapbox trace with a different color
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines",
                    lon=path_lons,
                    lat=path_lats,
                    line=dict(width=4, color='red'),
                    hoverinfo='none'
                )
            )

        # Add nodes as a Scattermapbox trace
        fig.add_trace(
            go.Scattermapbox(
                mode="markers+text",
                lon=df['lon'],
                lat=df['lat'],
                marker=go.scattermapbox.Marker(
                    size=9,
                    color='red'
                ),
                text=df['id'],
                textposition="top center",
                hoverinfo='text'
            )
        )

        # Update layout with the Mapbox access token
        fig.update_layout(
            mapbox=dict(
                accesstoken=mapbox_token,
                style="open-street-map",
                zoom=15,
                center=dict(lat=10.8510744, lon=106.7736178)  # Focus vào trường ĐH Sư phạm Kỹ thuật
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

        fig.show()

    def loadMapData(self):
        with open('./data/graph.json', 'r') as f:
            self.graph = json.load(f)
            for node in self.graph.keys():
                coordinate = self.graph[node]['info']['geometry']['coordinates']
                self.coordinates.append([coordinate[1], coordinate[0]])
                self.nodes.append(node)
            self.tree = KDTree(self.coordinates)
        with open('./data/building.json', 'r') as f:
            self.buildings = json.load(f)
            self.getAllBuildings()

    def getAllBuildings(self):
        all_buildings = []
        for id in self.buildings.keys():
            building = {}
            building['id'] = id
            building['name'] = self.buildings[id]['properties']['tags']['name']
            all_buildings.append(building)
        return all_buildings

    def getNearestNode(self, lat, lon):
        # Query the K-DTree for the nearest neighbor
        distance, index = self.tree.query([lat, lon])
        return self.nodes[index]  # return Node object

    def getDestination(self):
        return self.graph[self.nodes[0]]

    def getNodeCoordinateById(self, id):
        node = self.graph[id]["info"]["geometry"]["coordinates"]
        return node

    def getDistanceBetweenId(self, x, y):
        return haversine(self.getNodeCoordinateById(x)[1], self.getNodeCoordinateById(x)[0],
                         self.getNodeCoordinateById(y)[1], self.getNodeCoordinateById(y)[0])

    def getNeighbors(self, id):
        return self.graph[id]['neighbors']


if __name__ == '__main__':
    map_instance = Map()

    # Show the map
    map_instance.showMap(map_instance.nodes, map_instance.coordinates)
