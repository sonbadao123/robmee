import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            if d.get('step_index') == 441:
                print(d.get('content'))
        except:
            pass
