import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            idx = d.get('step_index')
            if d.get('type') == 'PLANNER_RESPONSE' and d.get('source') == 'MODEL':
                c = d.get('content', '')
                if any(k in c.lower() for k in ['e-0503', 'securityviolation', 'w2s', 'matrix', 'camera', 'driver']):
                    print(f"Step {idx} (len {len(c)}): {c[:300]}...\n---")
        except:
            pass
