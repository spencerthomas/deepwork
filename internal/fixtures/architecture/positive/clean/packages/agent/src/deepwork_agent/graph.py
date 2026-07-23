"""Independent agent may use public provider APIs."""

from langgraph.graph import StateGraph
from deepwork_agent._planning import value

GRAPH_TYPE = StateGraph
PLAN_VALUE = value
