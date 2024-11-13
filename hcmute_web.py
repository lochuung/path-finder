import streamlit as st
from simpleai.search import astar
from map import MapProblem, Map
from streamlit_plotly_events import plotly_events


def main():
    st.title("Tìm Đường Đi HCMUTE")

    # Khởi tạo map_instance và tải dữ liệu
    if 'map_instance' not in st.session_state:
        st.session_state.map_instance = Map()
    map_instance = st.session_state.map_instance

    # Lấy danh sách các tòa nhà và tạo dropdown
    buildings = map_instance.getAllBuildings()
    building_options = {b['id']: b['name'] for b in buildings}
    building_id = st.selectbox(
        "Chọn tòa nhà đích:",
        options=list(building_options.keys()),
        format_func=lambda x: building_options[x]
    )

    # Placeholder để cập nhật bản đồ
    map_placeholder = st.empty()

    # Kiểm tra xem đã có bản đồ trong session_state chưa
    if 'fig' not in st.session_state:
        fig, df = map_instance.createMapFigure(map_instance.nodes, map_instance.coordinates)
        st.session_state.fig = fig
        st.session_state.df = df
    else:
        fig = st.session_state.fig
        df = st.session_state.df

    # Chọn điểm xuất phát khi click vào bản đồ
    if 'source_id' not in st.session_state:
        st.session_state.source_id = None

    # Hiển thị bản đồ trong placeholder và xử lý sự kiện click
    with map_placeholder:
        selected_points = plotly_events(fig, click_event=True, override_height=600, override_width="100%")

    # Xử lý sự kiện click trên bản đồ
    if selected_points:
        point_data = selected_points[0]
        point_index = point_data['pointIndex']  # Sử dụng pointIndex để tìm source_id
        source_id = df.iloc[point_index]['id']  # Lấy source_id từ DataFrame
        st.session_state.source_id = source_id
        st.success(f"Đã chọn điểm xuất phát: {source_id}")

        # Cập nhật màu sắc của node được chọn
        for trace in fig['data']:
            if 'marker' in trace:
                trace['marker']['color'] = ['green' if node_id == source_id else 'red' for node_id in df['id']]
        st.session_state.fig = fig  # Lưu lại bản đồ đã cập nhật

        # Hiển thị bản đồ đã cập nhật
        with map_placeholder:
            selected_points = plotly_events(fig, click_event=True, override_height=600, override_width="100%")

    # Xử lý sự kiện tìm đường
    if st.button("Tìm Đường") and st.session_state.source_id and building_id:
        source_id = st.session_state.source_id

        # Thực hiện tìm đường
        destination_node = map_instance.getNearestNodeForBuilding(building_id, source_id)

        if destination_node is None:
            st.error("Không tìm thấy node nào của tòa nhà đích.")
        else:
            nearest_source_graph_node = None

            if not map_instance.getNeighbors(source_id):
                # Tạo cạnh giả giữa source_id và node gần nhất của đồ thị
                nearest_source_graph_node = map_instance.getNearestNodeInGraph(source_id)
                map_instance.addTemporaryConnection(source_id, nearest_source_graph_node)

            nearest_graph_node = map_instance.getNearestNodeInGraph(destination_node)
            map_instance.addTemporaryConnection(destination_node, nearest_graph_node)

            try:
                with st.spinner("Đang tìm đường..."):
                    problem = MapProblem(map_instance, source_id, destination_node)
                    result = astar(problem)
                    path = [step[1] for step in result.path()]

                    if not path:
                        st.error("Không tìm thấy đường đi.")
                    else:
                        st.success("Đã tìm thấy đường đi.")
                        # Cập nhật bản đồ với đường đi
                        new_fig, df = map_instance.createMapFigure(map_instance.nodes, map_instance.coordinates,
                                                                   path=path)
                        st.session_state.fig = new_fig  # Lưu lại bản đồ mới
                        st.session_state.df = df  # Cập nhật DataFrame nếu cần
            finally:
                map_instance.removeTemporaryConnection(destination_node, nearest_graph_node)
                if nearest_source_graph_node:
                    map_instance.removeTemporaryConnection(source_id, nearest_source_graph_node)
                st.session_state.source_id = None

        # Hiển thị bản đồ đã cập nhật
        with map_placeholder:
            selected_points = plotly_events(st.session_state.fig, click_event=True, override_height=600,
                                            override_width="100%")


if __name__ == '__main__':
    main()
