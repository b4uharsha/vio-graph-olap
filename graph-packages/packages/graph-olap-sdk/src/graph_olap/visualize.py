"""Interactive graph visualization for Jupyter notebooks.

Usage:
    from graph_olap import visualize
    visualize(wrapper_url, limit=200, title='My Graph')
"""

from __future__ import annotations

from typing import Optional

import requests

# Node colors by label — professional palette
_COLORS = [
    "#3B82F6",  # blue
    "#10B981",  # emerald
    "#F59E0B",  # amber
    "#EF4444",  # red
    "#8B5CF6",  # violet
    "#EC4899",  # pink
    "#06B6D4",  # cyan
    "#F97316",  # orange
    "#6366F1",  # indigo
    "#14B8A6",  # teal
    "#A855F7",  # purple
    "#84CC16",  # lime
]


def visualize(
    wrapper_url: str,
    limit: int = 200,
    height: str = "600px",
    title: str = "Graph",
    physics: bool = True,
) -> "IPython.display.HTML":
    """Render an interactive graph visualization in a Jupyter notebook.

    Parameters
    ----------
    wrapper_url : str
        The wrapper endpoint (e.g. http://wrapper-xxx:8000)
    limit : int
        Max relationships to show (default 200)
    height : str
        Height of the visualization (default 600px)
    title : str
        Title shown above the graph
    physics : bool
        Enable physics simulation (default True)

    Returns
    -------
    IPython.display.HTML object (renders inline in Jupyter)
    """
    from pyvis.network import Network
    from IPython.display import HTML
    import tempfile
    import os

    # Query the graph
    cypher = (
        f"MATCH (n)-[r]->(m) "
        f"RETURN id(n) AS src_id, labels(n)[0] AS src_label, "
        f"coalesce(n.name, n.title, n.hostname, toString(id(n))) AS src_name, "
        f"type(r) AS rel, "
        f"id(m) AS tgt_id, labels(m)[0] AS tgt_label, "
        f"coalesce(m.name, m.title, m.hostname, toString(id(m))) AS tgt_name "
        f"LIMIT {limit}"
    )
    resp = requests.post(f"{wrapper_url}/query", json={"query": cypher}, timeout=30)
    data = resp.json()

    if data.get("row_count", 0) == 0:
        print("No relationships found in this graph.")
        return HTML("<p style='color:#888;padding:20px;'>No data to visualize</p>")

    # Build pyvis network
    net = Network(
        height=height,
        width="100%",
        bgcolor="#06080d",
        font_color="#e4e4e7",
        notebook=True,
        cdn_resources="in_line",
    )

    if physics:
        net.barnes_hut(
            gravity=-8000,
            central_gravity=0.3,
            spring_length=150,
            spring_strength=0.01,
            damping=0.09,
        )
    else:
        net.toggle_physics(False)

    # Track labels for coloring
    label_colors: dict[str, str] = {}
    color_idx = 0
    nodes_added: set = set()

    for row in data["rows"]:
        src_id, src_label, src_name, rel, tgt_id, tgt_label, tgt_name = row

        # Assign colors by label
        if src_label not in label_colors:
            label_colors[src_label] = _COLORS[color_idx % len(_COLORS)]
            color_idx += 1
        if tgt_label not in label_colors:
            label_colors[tgt_label] = _COLORS[color_idx % len(_COLORS)]
            color_idx += 1

        # Add nodes
        if src_id not in nodes_added:
            display = src_name or f"{src_label} {src_id}"
            net.add_node(
                src_id,
                label=display,
                title=f"{src_label}: {display}",
                color=label_colors[src_label],
                size=22,
                font={"size": 11, "color": "#e4e4e7"},
            )
            nodes_added.add(src_id)

        if tgt_id not in nodes_added:
            display = tgt_name or f"{tgt_label} {tgt_id}"
            net.add_node(
                tgt_id,
                label=display,
                title=f"{tgt_label}: {display}",
                color=label_colors[tgt_label],
                size=22,
                font={"size": 11, "color": "#e4e4e7"},
            )
            nodes_added.add(tgt_id)

        # Add edge
        net.add_edge(
            src_id,
            tgt_id,
            title=rel,
            label=rel,
            color="rgba(100,120,160,0.4)",
            font={"size": 8, "color": "#6b7280"},
        )

    # Legend
    legend = " &nbsp;|&nbsp; ".join(
        [
            f'<span style="color:{c}; font-weight:600;">&#9679; {lbl}</span>'
            for lbl, c in label_colors.items()
        ]
    )

    # Render to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, dir="/tmp")
    net.save_graph(tmp.name)
    with open(tmp.name, "r") as f:
        html_content = f.read()
    os.unlink(tmp.name)

    header = (
        f'<div style="color:#e4e4e7; font-family:system-ui; font-size:13px; '
        f'margin-bottom:8px; padding:8px 0;">'
        f'<b style="font-size:15px;">{title}</b> &mdash; '
        f'{len(nodes_added)} nodes, {len(data["rows"])} edges'
        f'<br/><span style="font-size:12px;">{legend}</span></div>'
    )
    return HTML(header + html_content)
