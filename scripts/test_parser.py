import sys
sys.path.insert(0,'backend/src'); sys.path.insert(0,'ai_ml/src')
from syncnode_backend.api.v1.chat import _parse_tool_code_from_text

tests = [
    '<tool_code>computer_windows_search(query="Battery_Data.xlsx", file_path="C:\\syncnode\\workspace\\test.xlsx")</tool_code>',
    '<tool_code>excel_write_range(rows=[["BYD", "China", "Export", "LFP"], ["CATL", "China", "Export", "NCM"]], path="Battery_Data.xlsx", sheet_name="Specifications", start_cell="A10")</tool_code>',
    '<tool_code>computer_uia_click(window_title="Battery_Data", name="Close")</tool_code>',
    'Some text <tool_code>excel_write_range(path="test.xlsx", start_cell="A5", rows=[["a","b"],["c","d"]])</tool_code> after',
]
all_ok = True
for i, t in enumerate(tests):
    result = _parse_tool_code_from_text(t)
    ok = result and len(result) > 0
    status = 'PASS' if ok else 'FAIL'
    if not ok: all_ok = False
    print(f'{status} test {i+1}: {len(result)} tool(s)')
    for r in result:
        print('  fn:', r['function']['name'])
        print('  args keys:', list(r['function']['arguments'].keys()))
print()
print('ALL PASS' if all_ok else 'SOME FAILURES')
