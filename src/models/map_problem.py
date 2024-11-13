from simpleai.search import SearchProblem

from src.utils.haversine import haversine


class MapProblem(SearchProblem):
    def __init__(self, map_instance, source_id, destination_id):
        self.map = map_instance
        self.source_id = source_id
        self.destination_id = destination_id
        super().__init__(initial_state=source_id)

    def actions(self, state):
        return self.map.getNeighbors(state)

    def result(self, state, action):
        return action

    def is_goal(self, state):
        return state == self.destination_id

    def heuristic(self, state):
        current_coords = self.map.getNodeCoordinateById(state)
        destination_coords = self.map.getNodeCoordinateById(self.destination_id)
        return haversine(current_coords[1], current_coords[0], destination_coords[1], destination_coords[0])
