import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            idx = d.get('step_index')
            if 408 <= idx <= 440:
                c = d.get('content', '')
                tc = d.get('tool_calls')
                if tc:
                    for t in tc:
                        print(f"[{idx}] TOOL: {t.get('name')}\nCMD: {t.get('args').get('CommandLine') or t.get('args')}\n")
                elif c and d.get('source') == 'MODEL' and d.get('type') == 'GENERIC':
                    print(f"[{idx}] RESULT:\n{c[:400]}\n")
        except:
            pass
