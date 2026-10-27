"""
Component Dependency Graph (Feature F20).
Directed causal graph modeling physical and cyber dependencies in the EVSE system using NetworkX.
A link can only be proposed if a directed path exists between the event component and the affected signal.
"""

import networkx as nx
from typing import List, Optional, Tuple, Dict, Any


class ComponentDependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        # Nodes: components and physical signals
        nodes = [
            ("csms_backend", {"type": "component", "layer": "cyber_protocol", "label": "CSMS Backend"}),
            ("evse_controller", {"type": "component", "layer": "controller", "label": "EVSE Controller"}),
            ("power_converter", {"type": "component", "layer": "hardware", "label": "Power Converter (AC/DC)"}),
            ("cooling_system", {"type": "component", "layer": "hardware", "label": "Cooling System / Heat Exchanger"}),
            ("bms", {"type": "component", "layer": "controller", "label": "Battery Management System (BMS)"}),
            ("battery_pack", {"type": "component", "layer": "hardware", "label": "Battery Pack (Lithium-ion)"}),
            ("temperature_sensor", {"type": "component", "layer": "sensor", "label": "Temperature Sensor (NTC Thermistor)"}),
            ("current_sensor", {"type": "component", "layer": "sensor", "label": "Current Sensor (Hall Effect)"}),
            ("grid_interface", {"type": "component", "layer": "grid", "label": "Grid / Substation Feeder"}),

            # Physical Signals / Internal States
            ("charging_current", {"type": "signal", "layer": "physical", "label": "Charging Current (A)"}),
            ("battery_voltage", {"type": "signal", "layer": "physical", "label": "Terminal Voltage (V)"}),
            ("battery_soc", {"type": "signal", "layer": "physical", "label": "State of Charge (%)"}),
            ("battery_heating", {"type": "signal", "layer": "physical", "label": "Joule Heating Power (W)"}),
            ("battery_temperature", {"type": "signal", "layer": "physical", "label": "Battery Temperature (°C)"}),
            ("sensor_temperature", {"type": "signal", "layer": "sensor", "label": "Reported Sensor Temp (°C)"}),
            ("cooling_power", {"type": "signal", "layer": "physical", "label": "Cooling Dissipation (W)"}),
            ("grid_load", {"type": "signal", "layer": "grid", "label": "Grid Demand (kW)"}),
            ("bms_protection", {"type": "signal", "layer": "controller", "label": "BMS Protection Breaker"})
        ]
        self.graph.add_nodes_from(nodes)

        # Directed causal relationships
        edges = [
            # CSMS commands controller
            ("csms_backend", "evse_controller"),
            # Controller controls power converter and cooling
            ("evse_controller", "power_converter"),
            ("evse_controller", "cooling_system"),
            # Power converter drives electrical current
            ("power_converter", "charging_current"),
            # Current drives heating, voltage drop, SoC, sensors, and grid draw
            ("charging_current", "battery_heating"),
            ("charging_current", "battery_voltage"),
            ("charging_current", "battery_soc"),
            ("charging_current", "grid_load"),
            ("charging_current", "current_sensor"),
            # Heating increases battery temperature
            ("battery_heating", "battery_temperature"),
            # Cooling system directly influences battery temperature
            ("cooling_system", "cooling_power"),
            ("cooling_system", "battery_temperature"),
            ("cooling_power", "battery_temperature"),
            # Battery temperature triggers protection and feeds sensor
            ("battery_temperature", "bms_protection"),
            ("battery_temperature", "temperature_sensor"),
            ("temperature_sensor", "sensor_temperature"),
            # BMS limits and protection monitoring
            ("bms", "bms_protection"),
            # Grid interface
            ("grid_interface", "grid_load"),
            # Battery pack physical container
            ("battery_pack", "battery_temperature"),
            ("battery_pack", "battery_voltage")
        ]
        self.graph.add_edges_from(edges)

    def has_dependency_path(self, from_node: str, to_signal: str) -> bool:
        """Checks if a directed physical/causal path exists from source to target."""
        if from_node not in self.graph or to_signal not in self.graph:
            return False
        return nx.has_path(self.graph, from_node, to_signal)

    def find_shortest_path(self, from_node: str, to_signal: str) -> Optional[List[str]]:
        """Returns the shortest path sequence of components/signals if one exists."""
        try:
            if nx.has_path(self.graph, from_node, to_signal):
                return nx.shortest_path(self.graph, from_node, to_signal)
        except Exception:
            pass
        return None

    def get_graph_export(self) -> Dict[str, Any]:
        """Exports graph in node/edge format for frontend visualization."""
        nodes = [
            {
                "id": n,
                "label": self.graph.nodes[n].get("label", n),
                "type": self.graph.nodes[n].get("type", "component"),
                "layer": self.graph.nodes[n].get("layer", "hardware")
            }
            for n in self.graph.nodes()
        ]
        edges = [
            {"source": u, "target": v, "id": f"edge-{u}-{v}"}
            for u, v in self.graph.edges()
        ]
        return {"nodes": nodes, "edges": edges}


dependency_graph = ComponentDependencyGraph()
