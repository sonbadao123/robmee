import json

log_path = r'C:\Users\vphoa\.gemini\antigravity\brain\8db161d1-834b-4aa0-ada1-a6965ac58f7f\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            idx = data.get('step_index', 0)
            if 480 <= idx <= 765 and data.get('source') == 'MODEL' and data.get('type') == 'PLANNER_RESPONSE':
                content = data.get('content', '')
                if content and len(content) > 100:
                    print(f"=== STEP {idx} ===")
                    print(content[:1000])
                    print("\n" + "="*40 + "\n")
        except Exception as e:
            pass
