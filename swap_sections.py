
import os

file_path = r'e:\项目\币圈等监控系统\precious_metals_monitor.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find indices
# Chart Start: "<!-- 历史价差走势图"
chart_start_idx = -1
for i, line in enumerate(lines):
    if '<!-- 历史价差走势图' in line:
        chart_start_idx = i
        break

# Calculator Start: "<!-- Trading Calculator -->"
calc_start_idx = -1
for i, line in enumerate(lines):
    if '<!-- Trading Calculator -->' in line:
        calc_start_idx = i
        break

# Rules Start (End of Calculator): "<!-- Trading Rules -->"
rules_start_idx = -1
for i, line in enumerate(lines):
    if '<!-- Trading Rules -->' in line:
        rules_start_idx = i
        break

print(f"Chart Start Line: {chart_start_idx+1}")
print(f"Calc Start Line: {calc_start_idx+1}")
print(f"Rules Start Line: {rules_start_idx+1}")

if chart_start_idx != -1 and calc_start_idx != -1 and rules_start_idx != -1:
    # Extract blocks
    # Block 1 (Chart): lines[chart_start_idx : calc_start_idx]
    # includes the empty lines between them if any
    chart_block = lines[chart_start_idx : calc_start_idx]
    
    # Block 2 (Calc): lines[calc_start_idx : rules_start_idx]
    calc_block = lines[calc_start_idx : rules_start_idx]
    
    # Preceding content
    pre_content = lines[:chart_start_idx]
    # Following content
    post_content = lines[rules_start_idx:]
    
    # New content: Pre + Calc + Chart + Post
    new_lines = pre_content + calc_block + chart_block + post_content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Swap successful.")
else:
    print("Error: Could not locate all sections.")
