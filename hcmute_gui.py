import io
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

import dash_bootstrap_components as dbc
from PIL import Image, ImageTk
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from simpleai.search import astar

from src.models import Map, MapProblem


class PathfindingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tìm Đường Đi HCMUTE")

        # Khởi tạo map_instance và tải dữ liệu
        self.map_instance = Map()
        self.source_id = None
        self.destination_id = None
        self.fig, self.df = self.map_instance.createMapFigure(self.map_instance.nodes, self.map_instance.coordinates)

        # Tạo giao diện người dùng
        self.create_widgets()

        # Hiển thị bản đồ ban đầu
        self.display_map(self.fig)

        # Khởi động Dash trong một luồng riêng
        threading.Thread(target=self.run_dash_app, daemon=True).start()

    def create_widgets(self):
        # Dropdown chọn tòa nhà
        tk.Label(self.root, text="Chọn tòa nhà đích:").pack()
        self.building_var = tk.StringVar()
        self.buildings = {b['id']: b['name'] for b in self.map_instance.getAllBuildings()}
        self.building_dropdown = ttk.Combobox(self.root, textvariable=self.building_var,
                                              values=list(self.buildings.values()))
        self.building_dropdown.pack()

        # Nút chọn điểm xuất phát
        self.select_source_button = tk.Button(self.root, text="Chọn Điểm Xuất Phát", command=self.open_interactive_map)
        self.select_source_button.pack()

        # Nút tìm đường
        self.find_path_button = tk.Button(self.root, text="Tìm Đường", command=self.find_path)
        self.find_path_button.pack()

        # Canvas để hiển thị bản đồ
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

    def display_map(self, fig):
        # Xuất hình ảnh từ biểu đồ Plotly và hiển thị trên Tkinter Canvas
        img_data = fig.to_image(format="png")
        img = Image.open(io.BytesIO(img_data))
        self.map_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_img)

    def open_interactive_map(self):
        # Mở Dash app trong trình duyệt
        webbrowser.open("http://127.0.0.1:8050/")

    def run_dash_app(self):
        # Tạo ứng dụng Dash
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2("Tương tác Chọn Điểm Xuất Phát"),
                    dcc.Graph(
                        id='map-graph',
                        figure=self.fig,
                        config={'scrollZoom': True}
                    ),
                    html.Div(id='output-message', style={'marginTop': 20})
                ])
            ])
        ])

        @app.callback(
            Output('output-message', 'children'),
            Input('map-graph', 'clickData')
        )
        def select_source_node(clickData):
            if clickData is None:
                return "Chưa chọn điểm nào."
            point_data = clickData['points'][0]
            point_index = point_data['pointIndex']
            self.source_id = self.df.iloc[point_index]['id']
            return f"Đã chọn điểm xuất phát: {self.source_id}"

        app.run_server(debug=False, use_reloader=False)

    def find_path(self):
        # Lấy tòa nhà đích từ dropdown
        building_name = self.building_var.get()
        building_id = None
        for key, value in self.buildings.items():
            if value == building_name:
                building_id = key
                break

        if not self.source_id:
            messagebox.showwarning("Chọn Điểm Xuất Phát", "Vui lòng chọn điểm xuất phát.")
            return

        if not building_id:
            messagebox.showwarning("Chọn Tòa Nhà Đích", "Vui lòng chọn tòa nhà đích.")
            return

        # Thực hiện tìm đường trong luồng riêng
        threading.Thread(target=self.run_astar_search, args=(building_id,), daemon=True).start()

        # Hiển thị thông báo cho người dùng
        messagebox.showinfo("Tìm Đường", "Đang tìm đường...")
        self.find_path_button.config(state=tk.DISABLED)

    def run_astar_search(self, building_id):
        destination_node = self.map_instance.getNearestNodeForBuilding(building_id, self.source_id)
        if destination_node is None:
            messagebox.showerror("Lỗi", "Không tìm thấy node nào của tòa nhà đích.")
            return

        nearest_source_graph_node = None
        if not self.map_instance.getNeighbors(self.source_id):
            nearest_source_graph_node = self.map_instance.getNearestNodeInGraph(self.source_id)
            self.map_instance.addTemporaryConnection(self.source_id, nearest_source_graph_node)

        nearest_graph_node = self.map_instance.getNearestNodeInGraph(destination_node)
        self.map_instance.addTemporaryConnection(destination_node, nearest_graph_node)

        try:
            problem = MapProblem(self.map_instance, self.source_id, destination_node)
            result = astar(problem)
            path = [step[1] for step in result.path()]

            if not path:
                messagebox.showinfo("Kết Quả", "Không tìm thấy đường đi.")
            else:
                messagebox.showinfo("Kết Quả", "Đã tìm thấy đường đi.")
                # Cập nhật bản đồ với đường đi
                new_fig, _ = self.map_instance.createMapFigure(self.map_instance.nodes, self.map_instance.coordinates,
                                                               path=path)
                self.display_map(new_fig)
        finally:
            self.map_instance.removeTemporaryConnection(destination_node, nearest_graph_node)
            if nearest_source_graph_node:
                self.map_instance.removeTemporaryConnection(self.source_id, nearest_source_graph_node)
            self.source_id = None
            self.find_path_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = PathfindingApp(root)
    root.mainloop()
