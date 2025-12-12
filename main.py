from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collections import defaultdict, deque
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class Node(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Optional[Dict[str, Any]] = {}

class Edge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class PipelineRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}

@app.post('/pipelines/parse')
def parse_pipeline(pipeline: PipelineRequest):
    try:
        nodes = pipeline.nodes
        edges = pipeline.edges
        
        # Count nodes and edges
        num_nodes = len(nodes)
        num_edges = len(edges)
        
        # Build adjacency list and in-degree count for DAG detection
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize in-degree for all nodes
        for node in nodes:
            in_degree[node.id] = 0
            
        # Build graph
        for edge in edges:
            if edge.source and edge.target:
                adjacency[edge.source].append(edge.target)
                if edge.target in in_degree:
                    in_degree[edge.target] += 1
                else:
                    in_degree[edge.target] = 1
        
        # Kahn's algorithm for topological sort (DAG detection)
        # Find all nodes with no incoming edges
        queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
        visited_count = 0
        
        while queue:
            current_node = queue.popleft()
            visited_count += 1
            
            # Reduce in-degree for all neighbors
            for neighbor in adjacency[current_node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If we visited all nodes, it's a DAG (no cycles)
        is_dag = visited_count == len(nodes)
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "is_dag": is_dag
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing pipeline: {str(e)}")