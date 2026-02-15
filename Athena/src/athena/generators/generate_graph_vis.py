#!/usr/bin/env python3
"""
Generate Graph Visualization (Vis.js)
=====================================
Scans the workspace for markdown files and internal links, then generates
a standalone HTML file with an interactive Vis.js network graph.

Usage: python3 generate_graph_vis.py
"""

import os
import re
import json
import sys
from collections import defaultdict
from urllib.parse import unquote

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, ".context", "memories", "visualizations", "athena_graph_live.html")

# Directories to scan
SCAN_DIRS = [
    os.path.join(PROJECT_ROOT, ".context"),
    os.path.join(PROJECT_ROOT, ".agent"),
    os.path.join(PROJECT_ROOT, ".framework"),
]

# Exclusions
EXCLUDED_DIRS = [
    "session_logs",
    "journals",
    "graphrag_env",
    "cache",
    ".git"
]

# Color Mapping by path keyword
COLOR_MAP = {
    "core": "#ffffff",        # Core Identity
    "protocols": "#ff6b6b",   # Red (Actions)
    "case_studies": "#95e1d3",# Teal (Evidence)
    "patterns": "#ffe66d",    # Yellow (Frameworks)
    "framework": "#4ecdc4",   # Cyan (Architecture)
    "profile": "#c7f9cc",     # Light Green (User)
    "default": "#a8a8b3"      # Grey (Generic)
}

def get_all_md_files():
    """Recursively find all .md files in scan directories."""
    md_files = []
    for root_dir in SCAN_DIRS:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))
    return md_files

def normalize_path(path):
    """Normalize a path for comparison."""
    if path.startswith("file://"):
        path = path.replace("file://", "")
    path = unquote(path)
    path = path.split('#')[0].strip()
    return path

def extract_links(file_path):
    """Extract all markdown links from a file."""
    link_pattern = re.compile(r'\[.*?\]\((?!http|mailto)(.*?)\)')
    links = []
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        matches = link_pattern.findall(content)
        for link in matches:
            normalized = normalize_path(link)
            if normalized:
                # Resolve relative to file
                abs_link = os.path.normpath(os.path.join(os.path.dirname(file_path), normalized))
                if os.path.exists(abs_link):
                    links.append(abs_link)
                # Fallback: check relative to root
                elif os.path.exists(os.path.join(PROJECT_ROOT, normalized)):
                    links.append(os.path.join(PROJECT_ROOT, normalized))
    except Exception:
        pass # Ignore read errors
    
    return links

def determine_group(path):
    """Determine node group/color based on path."""
    lower_path = path.lower()
    if "core_identity" in lower_path: return "core"
    if "protocols" in lower_path: return "protocols"
    if "case_studies" in lower_path: return "case_studies"
    if "patterns" in lower_path: return "patterns"
    if ".framework" in lower_path: return "framework"
    if "profile" in lower_path: return "profile"
    return "default"

def generate_html(nodes, edges):
    """Generate the HTML content."""
    
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Athena Live Graph | {len(nodes)} Nodes</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background: #1a1a2e; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
        #graph {{ width: 100vw; height: 100vh; }}
        #info {{ position: fixed; top: 20px; left: 20px; color: #eee; background: rgba(0,0,0,0.85); 
                padding: 20px; border-radius: 12px; max-width: 300px; backdrop-filter: blur(5px); border: 1px solid #333; }}
        h2 {{ margin: 0 0 10px 0; color: #4ecdc4; font-size: 18px; }}
        p {{ margin: 5px 0; font-size: 13px; line-height: 1.4; color: #ccc; }}
        .stat {{ font-weight: bold; color: #fff; }}
        .legend {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #444; }}
        .legend-item {{ display: flex; align-items: center; margin: 4px 0; font-size: 11px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }}
    </style>
</head>
<body>
    <div id="info">
        <h2>🧠 Athena Neural Map</h2>
        <p>Live visualization of the active workspace.</p>
        <p>Nodes: <span class="stat">{len(nodes)}</span></p>
        <p>Connections: <span class="stat">{len(edges)}</span></p>
        <div class="legend">
            <div class="legend-item"><div class="legend-dot" style="background:#ffffff"></div>Core Identity</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ff6b6b"></div>Protocols (Action)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#95e1d3"></div>Case Studies (Data)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ffe66d"></div>Patterns (Frameworks)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#a8a8b3"></div>General Knowledge</div>
        </div>
        <p style="margin-top:15px; font-size:10px; opacity:0.6">use scroll to zoom • drag to pan</p>
    </div>
    <div id="graph"></div>
    <script>
        const nodes = new vis.DataSet({nodes_json});
        const edges = new vis.DataSet({edges_json});
        
        const container = document.getElementById('graph');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            nodes: {{ 
                shape: 'dot', 
                font: {{ size: 14, color: '#ffffff', face: 'Segoe UI' }}, 
                borderWidth: 1,
                shadow: true,
                scaling: {{ min: 10, max: 60 }}
            }},
            edges: {{ 
                width: 1, 
                color: {{ color: 'rgba(255,255,255,0.15)', highlight: '#4ecdc4' }}, 
                smooth: {{ type: 'continuous', roundness: 0 }} 
            }},
            physics: {{
                stabilization: {{ iterations: 200 }},
                barnesHut: {{
                    gravitationalConstant: -3000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.1
                }}
            }},
            interaction: {{ 
                hover: true, 
                tooltipDelay: 200,
                hideEdgesOnDrag: true
            }}
        }};
        
        const network = new vis.Network(container, data, options);
        
        network.on("click", function (params) {{
            // console.log(params);
        }});
    </script>
</body>
</html>
"""
    return html_template

def main():
    print("🔍 Scanning workspace for knowledge nodes...")
    files = get_all_md_files()
    
    nodes = []
    edges = []
    
    # Path to ID mapping
    path_to_id = {}
    
    # Pass 1: Create Nodes
    for i, file_path in enumerate(files):
        abs_path = os.path.abspath(file_path)
        path_to_id[abs_path] = i
        
        filename = os.path.basename(file_path)
        group = determine_group(file_path)
        
        # Calculate approximate weight (size) based on inbound links later, 
        # for now initialized defaults
        nodes.append({
            "id": i,
            "label": filename.replace(".md", ""),
            "title": abs_path, # Tooltip
            "color": COLOR_MAP.get(group, "#a8a8b3"),
            "value": 1 # Base size
        })
        
    print(f"✅ Found {len(nodes)} nodes.")
    
    # Pass 2: Create Edges
    print("🔗 Linking concepts...")
    edge_count = 0
    inbound_counts = defaultdict(int)
    
    for file_path in files:
        source_id = path_to_id.get(os.path.abspath(file_path))
        if source_id is None: continue
        
        links = extract_links(file_path)
        for link in links:
            target_id = path_to_id.get(link)
            if target_id is not None and target_id != source_id:
                edges.append({
                    "from": source_id,
                    "to": target_id
                })
                inbound_counts[target_id] += 1
                edge_count += 1
                
    # Update node sizes based on centrality (inbound links)
    for node in nodes:
        node_id = node["id"]
        count = inbound_counts[node_id]
        # Size formula: base + (links * multiplier)
        node["value"] = 5 + (count * 2)
        
        # High value nodes get special treatment if not already colored special
        if count > 10 and node["color"] == "#a8a8b3":
             node["color"] = "#ffffff" # Highlight hubs
             
    print(f"✅ Created {edge_count} connections.")
    
    # Generate HTML
    html_content = generate_html(nodes, edges)
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(html_content)
        
    print(f"🚀 Visualization saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
