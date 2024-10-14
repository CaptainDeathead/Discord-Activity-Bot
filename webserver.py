import flask

from analytics import GraphManager

class WebServer:
    def __init__(self, graph_manager: GraphManager, port: int) -> None:
        self.graph_manager = graph_manager 
        self.port = port

        self.app = flask.Flask(__name__)
        self.setup_routes()
        
        self.app.run(host='0.0.0.0', port=port)
        
    def setup_routes(self) -> None:
        @self.app.route('/simple_status_graph')
        def simple_status_graph():
            user = flask.request.args.get('user')

            if user is None: return flask.send_from_directory('images', 'user_not_specified.png')

            user_id = self.graph_manager.get_user_id(user)

            if user_id is None: return flask.send_from_directory('images', 'user_not_found.png')

            graph_file: str = self.graph_manager.get_user_simple_time(user_id, user)

            if graph_file == "":
                return f"{user} is not found in the database. Please DM @captaindeathead for assistance."
            else:
                return flask.send_file(graph_file)

        @self.app.route('/rich_status_graph')
        def rich_status_graph():
            ...

        @self.app.route('/rich_status_table')
        def rich_status_table():
            ...

        @self.app.route('/select_compare_simple_status_graph')
        def select_compare_simple_status_graph():
            ...

        @self.app.route('/select_compare_rich_status_graph')
        def select_compare_rich_status_graph():
            ...

        @self.app.route('/select_server_rich_status_graph')
        def select_server_rich_status_graph():
            ...

        @self.app.route('/weekly_simple_status_gain_graph')
        def weekly_simple_status_gain_graph():
            ...

        @self.app.route('/weekly_rich_status_gain_graph')
        def weekly_rich_status_gain_graph():
            ...
