import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            idx = d.get('step_index')
            if 407 <= idx <= 450:
                c = d.get('content', '')
                tc = d.get('tool_calls')
                if tc:
                    print(f"[{idx}] TOOL: {[x.get('name') for x in tc]} args: {[str(x.get('args'))[:120] for x in tc]}")
                elif c and d.get('source') == 'MODEL' and d.get('type') == 'PLANNER_RESPONSE':
                    print(f"=== MODEL {idx} ===")
                    print(c[:1000])
                    print("\n" + "="*40 + "\n")
        except:
            pass
