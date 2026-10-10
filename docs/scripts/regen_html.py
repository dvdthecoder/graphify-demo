import json, re, sys, collections
import networkx as nx
from pathlib import Path
from graphify.exporters.html import to_html

LABELS = {
 0: "Bid Review Agent Design", 1: "DB Core & Spec Doc Shape", 2: "Report Sparklines", 3: "Document Harvesting",
 4: "Spec Dictionary & Tech Reqs", 5: "Classify & Report Generation", 6: "Line Item Parsing & Status",
 7: "DB Query Layer", 8: "Pydantic AI Orchestrator", 9: "Demand Fit Analysis", 10: "DB Upserts & Ingest",
 11: "MVP Bid Resolution", 12: "Spec Completeness Skill", 13: "Bid Review MCP Server",
 14: "Platform & Weight Classifiers", 15: "Capability Text Parsing", 16: "Keyword Bid Scraping",
 17: "LLM Pipeline Stage 4", 18: "Line Item Use Case & Specs", 19: "LLM Spec Mining",
 20: "Pipeline Run Tracking", 21: "VTOL Category Audit", 22: "Quote Verification Tests",
 23: "Airframe Vocabulary Tests", 24: "Capability Explanation Grouping", 25: "Capability Explanation Phrasing",
 26: "Airframe Fallback Gate", 27: "Component Taxonomy Ingest", 28: "Whitespace Normalization Tests",
 29: "OpenWebUI Pipeline Wrapper", 30: "Keyword & Taxonomy Seeding", 31: "Bid Facts Mining",
 32: "Buyer Type Classifier", 33: "OCR Recovery", 34: "Boilerplate Quote Tests", 35: "Bid Classification Feed",
 36: "Component Demand Query", 37: "Harvested Bid Lookup", 38: "Recent Pipeline Runs",
 39: "Modal Serving Concepts", 40: "Modal Smoke Tests", 41: "GPU Serving Profiles",
 42: "Modal Apps & Secrets", 43: "Qwen3 vLLM Servers", 44: "Laya T4 Server", 45: "modal-io-serve Package",
}
src = Path(sys.argv[1]); out = Path(sys.argv[2])
d = json.loads(src.read_text())
for n in d["nodes"]:
    n["community_name"] = LABELS.get(n["community"], f"Community {n['community']}")
src.write_text(json.dumps(d, indent=2, ensure_ascii=False))

G = nx.node_link_graph(d, edges="links")
comms = collections.defaultdict(list)
for n, a in G.nodes(data=True):
    comms[a["community"]].append(n)
to_html(G, dict(comms), str(out), community_labels=LABELS)
# graphify labels only nodes with degree >= 15% of max; give every node a label.
# vis-network skips drawing labels too small on screen, so they appear as you zoom in.
h = out.read_text()
h, k = re.subn(r'"font": \{"size": 0,', '"font": {"size": 12,', h)
out.write_text(h)
print(f"wrote {out}, {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {k} labels enabled")
