import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import KDTree

from src.config import MAPBOX_TOKEN, DEFAULT_ZOOM, DEFAULT_CENTER
from src.utils.haversine import haversine


class Map:
    def __init__(self):
        self.graph = {}
        self.tree = None
        self.coordinates = []
        self.nodes = []
        self.loadMapData()

    def createMapFigure(self, nodes, coordinates, path=None):
        px.set_mapbox_access_token(MAPBOX_TOKEN)
        mapData = []
        for i in range(len(nodes)):
            mapData.append([nodes[i], coordinates[i][0], coordinates[i][1]])
        df = pd.DataFrame(mapData, columns=['id', 'lat', 'lon'])
        edge_lats = []
        edge_lons = []
        for node_id, node_info in self.graph.items():
            node_coord = self.getNodeCoordinateById(node_id)
            for neighbor_id in node_info['neighbors']:
                neighbor_coord = self.getNodeCoordinateById(neighbor_id)
                edge_lats += [node_coord[1], neighbor_coord[1], None]
                edge_lons += [node_coord[0], neighbor_coord[0], None]
        fig = go.Figure()
        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=edge_lons,
                lat=edge_lats,
                line=dict(width=2, color='blue'),
                hoverinfo='none'
            )
        )
        if path:
            path_lats = []
            path_lons = []
            for i in range(len(path) - 1):
                start_coord = self.getNodeCoordinateById(path[i])
                end_coord = self.getNodeCoordinateById(path[i + 1])
                path_lats += [start_coord[1], end_coord[1], None]
                path_lons += [start_coord[0], end_coord[0], None]
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines",
                    lon=path_lons,
                    lat=path_lats,
                    line=dict(width=4, color='red'),
                    hoverinfo='none'
                )
            )
            # Tính toán trung tâm và mức độ zoom dựa trên đường đi
            valid_lats = [lat for lat in path_lats if lat is not None]
            valid_lons = [lon for lon in path_lons if lon is not None]
            min_lat = min(valid_lats)
            max_lat = max(valid_lats)
            min_lon = min(valid_lons)
            max_lon = max(valid_lons)
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            # Tính toán delta để xác định mức độ zoom
            delta_lat = max_lat - min_lat
            delta_lon = max_lon - min_lon
            max_delta = max(delta_lat, delta_lon)
            # Thiết lập mức độ zoom dựa trên kích thước của đường đi
            if max_delta < 0.001:
                zoom = 18
            elif max_delta < 0.005:
                zoom = 17
            elif max_delta < 0.01:
                zoom = 16
            elif max_delta < 0.02:
                zoom = 15
            elif max_delta < 0.05:
                zoom = 14
            elif max_delta < 0.1:
                zoom = 13
            elif max_delta < 0.2:
                zoom = 12
            else:
                zoom = 11
        else:
            center_lat = DEFAULT_CENTER['lat']
            center_lon = DEFAULT_CENTER['lon']
            zoom = DEFAULT_ZOOM
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=df['lon'],
                lat=df['lat'],
                marker=go.scattermapbox.Marker(
                    size=9,
                    color='red'
                ),
                text=df['id'],
                hoverinfo='text',
                customdata=df['id'],
            )
        )
        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style="open-street-map",
                zoom=zoom,
                center=dict(lat=center_lat, lon=center_lon)
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        return fig, df

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

    def getAllBuildings(self):
        all_buildings = []
        for id in self.buildings.keys():
            building = {}
            building['id'] = id
            building['name'] = self.buildings[id]['properties']['tags']['name']
            all_buildings.append(building)
        return all_buildings

    def getNearestNode(self, lat, lon):
        distance, index = self.tree.query([lat, lon])
        return self.nodes[index]

    def getNodeCoordinateById(self, id):
        node = self.graph[id]["info"]["geometry"]["coordinates"]
        return node

    def getDistanceBetweenId(self, x, y):
        return haversine(self.getNodeCoordinateById(x)[1], self.getNodeCoordinateById(x)[0],
                         self.getNodeCoordinateById(y)[1], self.getNodeCoordinateById(y)[0])

    def getNeighbors(self, id):
        return self.graph[id]['neighbors']

    def getNearestNodeForBuilding(self, building_id, source_node_id):
        building_nodes = self.buildings[building_id]['properties']['nodes']
        source_coords = self.getNodeCoordinateById(source_node_id)
        nearest_node = None
        min_distance = float('inf')
        for node_id in building_nodes:
            node_id = str(node_id)
            if node_id in self.graph:
                target_coords = self.getNodeCoordinateById(node_id)
                distance = haversine(source_coords[1], source_coords[0], target_coords[1], target_coords[0])
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id
        return nearest_node

    def getNearestNodeInGraph(self, target_node_id):
        target_coords = self.getNodeCoordinateById(target_node_id)
        min_distance = float('inf')
        nearest_node = None
        for node_id in self.graph.keys():
            if node_id != target_node_id and self.getNeighbors(node_id):
                graph_node_coords = self.getNodeCoordinateById(node_id)
                distance = haversine(target_coords[1], target_coords[0], graph_node_coords[1], graph_node_coords[0])
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id
        return nearest_node

    def addTemporaryConnection(self, node1, node2):
        if node1 not in self.graph:
            self.graph[node1] = {'neighbors': []}
        if node2 not in self.graph:
            self.graph[node2] = {'neighbors': []}
        self.graph[node1]['neighbors'].append(node2)
        self.graph[node2]['neighbors'].append(node1)

    def removeTemporaryConnection(self, node1, node2):
        if node1 in self.graph and node2 in self.graph[node1]['neighbors']:
            self.graph[node1]['neighbors'].remove(node2)
        if node2 in self.graph and node1 in self.graph[node2]['neighbors']:
            self.graph[node2]['neighbors'].remove(node1)
