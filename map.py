import json
import math
from scipy.spatial import KDTree
from simpleai.search import SearchProblem, astar
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def haversine(lat1, lon1, lat2, lon2):
    """
        Tính khoảng cách giữa hai điểm trên bề mặt Trái Đất.

        Tham số:
        lat1, lon1: Vĩ độ và kinh độ của điểm thứ nhất (đơn vị: độ)
        lat2, lon2: Vĩ độ và kinh độ của điểm thứ hai (đơn vị: độ)

        Trả về:
        Khoảng cách giữa hai điểm (đơn vị: km)
        """
    # Bán kính trung bình của Trái Đất theo km
    R = 6371.0

    # Chuyển đổi độ sang radian
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Hiệu số giữa các tọa độ
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Công thức Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Tính khoảng cách
    distance = R * c
    return distance


class Map:
    def __init__(self):
        self.graph = {}
        self.tree = None
        self.coordinates = []
        self.nodes = []
        self.loadMapData()

    def createMapFigure(self, nodes, coordinates, path=None):
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

        # Add nodes as a Scattermapbox trace with click events
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
                customdata=df['id'],  # Dùng customdata để lưu trữ id node
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

        return fig

    def showMap(self, nodes, coordinates, path=None):

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

    def getNearestNodeForBuilding(self, building_id, source_node_id):
        # Lấy danh sách các nodes của building
        building_nodes = self.buildings[building_id]['properties']['nodes']
        source_coords = self.getNodeCoordinateById(source_node_id)

        # Tìm node gần nhất trong các nodes của building so với source_id
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
        """Tìm node gần nhất trong đồ thị cho một node cụ thể."""
        target_coords = self.getNodeCoordinateById(target_node_id)
        min_distance = float('inf')
        nearest_node = None

        for node_id in self.graph.keys():
            if node_id != target_node_id and self.getNeighbors(node_id):  # Không xét chính node đích
                graph_node_coords = self.getNodeCoordinateById(node_id)
                distance = haversine(target_coords[1], target_coords[0], graph_node_coords[1], graph_node_coords[0])
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id

        return nearest_node

    def addTemporaryConnection(self, node1, node2):
        """Thêm kết nối tạm thời giữa hai nodes."""
        if node1 not in self.graph:
            self.graph[node1] = {'neighbors': []}
        if node2 not in self.graph:
            self.graph[node2] = {'neighbors': []}

        # Kết nối hai nodes lại với nhau
        self.graph[node1]['neighbors'].append(node2)
        self.graph[node2]['neighbors'].append(node1)

    def removeTemporaryConnection(self, node1, node2):
        """Loại bỏ kết nối tạm thời giữa hai nodes."""
        if node1 in self.graph and node2 in self.graph[node1]['neighbors']:
            self.graph[node1]['neighbors'].remove(node2)
        if node2 in self.graph and node1 in self.graph[node2]['neighbors']:
            self.graph[node2]['neighbors'].remove(node1)


class MapProblem(SearchProblem):
    def __init__(self, map_instance, source_id, destination_id):
        self.map = map_instance
        self.source_id = source_id
        self.destination_id = destination_id
        super().__init__(initial_state=source_id)

    def actions(self, state):
        # Trả về danh sách các node láng giềng (hàng xóm) của node hiện tại
        return self.map.getNeighbors(state)

    def result(self, state, action):
        # Trả về trạng thái mới sau khi di chuyển đến node láng giềng
        return action

    def is_goal(self, state):
        # Kiểm tra xem node hiện tại có phải là điểm đích hay không
        return state == self.destination_id

    def heuristic(self, state):
        # Sử dụng khoảng cách haversine giữa state hiện tại và điểm đích làm heuristic
        current_coords = self.map.getNodeCoordinateById(state)
        destination_coords = self.map.getNodeCoordinateById(self.destination_id)
        return haversine(current_coords[1], current_coords[0], destination_coords[1], destination_coords[0])


if __name__ == '__main__':
    map_instance = Map()

    # Xác định ID nút nguồn và ID tòa nhà đích
    source_id = "5125105355"
    building_id = "239828231"  # Tòa trung tâm

    # Lấy node gần nhất của building từ source_id
    destination_node = map_instance.getNearestNodeForBuilding(building_id, source_id)

    if destination_node is None:
        print(f"Không tìm thấy node nào của tòa nhà {building_id}")
        exit()

    nearest_source_graph_node = None

    if not map_instance.getNeighbors(source_id):
        # Tạo cạnh giả giữa source_id và node gần nhất của đồ thị
        nearest_source_graph_node = map_instance.getNearestNodeInGraph(source_id)
        map_instance.addTemporaryConnection(source_id, nearest_source_graph_node)

    # Tìm node gần nhất trong đồ thị so với destination_node
    nearest_graph_node = map_instance.getNearestNodeInGraph(destination_node)

    # Thêm cạnh giả giữa destination_node và nearest_graph_node
    map_instance.addTemporaryConnection(destination_node, nearest_graph_node)

    # map_instance.showMap(map_instance.nodes, map_instance.coordinates)

    try:
        # Tạo đối tượng MapProblem với destination_node là đích
        problem = MapProblem(map_instance, source_id, destination_node)

        # Chạy thuật toán A* để tìm đường đi
        result = astar(problem)

        # Lấy đường đi từ kết quả
        path = [step[1] for step in result.path()]  # Lấy danh sách các node trong đường đi

        if path:
            print(f"Đường đi từ node {source_id} đến node {destination_node}:")
            print(path)
        else:
            print(f"Không tìm thấy đường đi từ node {source_id} đến node {destination_node}")
            exit()

        # Hiển thị đường đi trên bản đồ
        map_instance.showMap(map_instance.nodes, map_instance.coordinates, path=path)
    finally:
        # Xóa kết nối tạm thời sau khi hoàn thành
        map_instance.removeTemporaryConnection(destination_node, nearest_graph_node)
        if nearest_source_graph_node:
            map_instance.removeTemporaryConnection(source_id, nearest_source_graph_node)
