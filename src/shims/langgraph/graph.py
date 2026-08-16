# langgraph/graph.py

import logging

END = "__END__"

class StateGraph:
    def __init__(self, state_schema):
        self.state_schema = state_schema
        self.nodes = {}
        self.edges = []
        self.entry_point = None

    def add_node(self, name, node_func):
        self.nodes[name] = node_func

    def set_entry_point(self, name):
        self.entry_point = name

    def add_edge(self, node_from, node_to):
        self.edges.append((node_from, node_to))

    def compile(self):
        return CompiledGraph(self)

class CompiledGraph:
    def __init__(self, graph):
        self.graph = graph

    async def ainvoke(self, initial_state):
        state = initial_state.copy()
        current_node = self.graph.entry_point
        visited = set()
        
        while current_node and current_node != END:
            if current_node in visited:
                break
            visited.add(current_node)
            
            if current_node not in self.graph.nodes:
                break
                
            node_func = self.graph.nodes[current_node]
            try:
                result = await node_func(state)
                if isinstance(result, dict):
                    for k, v in result.items():
                        if k == "market_data" and "market_data" in state:
                            state["market_data"] = {**state["market_data"], **v}
                        else:
                            state[k] = v
            except Exception as e:
                logging.error(f"LangGraph node {current_node} execution failed: {e}")
                raise e
            
            next_node = None
            for edge_from, edge_to in self.graph.edges:
                if edge_from == current_node:
                    next_node = edge_to
                    break
            current_node = next_node
            
        return state
