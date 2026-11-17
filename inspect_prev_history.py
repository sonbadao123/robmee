import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            idx = d.get('step_index')
            if 750 <= idx <= 796:
                src = d.get('source')
                tp = d.get('type')
                tc = d.get('tool_calls')
                c = d.get('content', '')
                if tp == 'USER_INPUT':
                    print(f"\n=== USER INPUT ({idx}) ===")
                    print(c)
                elif c and not tc:
                    print(f"\n=== MODEL RESPONSE ({idx}) ===")
                    print(c[:400])
                elif tc:
                    tool_names = [x.get('name') for x in tc]
                    print(f"[{idx}] TOOL: {tool_names}")
        except Exception as e:
            pass
