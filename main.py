from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collections import defaultdict, deque
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
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
def health_check():
    return {"message": "Backend is running"}

@app.post('/pipelines/parse')
def parse_pipeline(pipeline: PipelineRequest):
    try:
        nodes = pipeline.nodes
        edges = pipeline.edges
        
        # Count nodes and edges
        num_nodes = len(nodes)
        num_edges = len(edges)
        
        # Get all node IDs (from both nodes and edges)
        all_node_ids = set()
        for node in nodes:
            all_node_ids.add(node.id)
        for edge in edges:
            if edge.source:
                all_node_ids.add(edge.source)
            if edge.target:
                all_node_ids.add(edge.target)
        
        # Build graph structure
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize in-degree for all nodes
        for node_id in all_node_ids:
            in_degree[node_id] = 0
            
        # Create graph connections
        for edge in edges:
            if edge.source in all_node_ids and edge.target in all_node_ids:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Check if graph is a DAG (no cycles)
        queue = deque([node_id for node_id in all_node_ids if in_degree[node_id] == 0])
        visited_count = 0
        
        while queue:
            current_node = queue.popleft()
            visited_count += 1
            
            for neighbor in adjacency[current_node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If all nodes visited, it's a DAG
        is_dag = visited_count == len(all_node_ids)
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "is_dag": is_dag
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")