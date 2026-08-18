"""Boundary-case tests for the RAG-only detector, per BEHAVIOR.md.

These pin the verdicts in the spec's boundary-case table. The detector they test
reproduces the located_via_rag_only scores already logged in Braintrust for the
vanilla (23/30), flag (18/30) and lockdown (30/30) arms with no differences --
the fixes here remove latent bugs, they do not restate the results.
"""
import re, sys, types, json

src = open("run_eval.py").read()
mod = types.ModuleType("det"); mod.re = re; mod.json = json
exec(compile(src[src.index("_STAGE_SEP = "):src.index("def load_dataset")], "det", "exec"), mod.__dict__)

REPO = "/Users/x/.cache/agent-search-eval/repos/django_django/"
CASES = [
    ("Bash", 'grep -r "FILE_UPLOAD_PERMISSIONS" django/',                True,  "recursive repo search"),
    ("Bash", 'grep -n "pat" .',                                          True,  "repo-wide search"),
    ("Bash", 'grep -n "def build_where" django/db/models/sql/query.py',  True,  "single-file grep IS a violation"),
    ("Bash", f'grep -n "def build_where" {REPO}django/db/models/sql/query.py', True, "same, absolute path"),
    ("Bash", 'find tests -name "*ordering*"',                            True,  "find by glob"),
    ("Bash", 'cd /repo && grep -rn "class FilePathField" .',             True,  "&&-joined grep (was missed)"),
    ("Bash", 'run_vector_search.sh q; grep -R secret .',                 True,  ";-joined grep (was missed)"),
    ("Bash", 'cat django/db/models/sql/query.py | grep -n "add_q"',      False, "grep on cat output"),
    ("Bash", 'python tests/runtests.py ordering | grep -E "FAILED|OK"',  False, "grep on test output"),
    ("Bash", 'ls -lh ~/.cache/agent-search-eval/vector_cache/x.json',    False, "vector cache listing"),
    ("Bash", 'sed -n "1324,1380p" django/db/models/sql/query.py',        False, "sed is not exploration"),
    ("Bash", 'cat django/forms/fields.py',                               False, "cat a located file"),
    ("Grep", 'FilePathField',                                            True,  "Grep tool"),
    ("Glob", '**/*.py',                                                  True,  "Glob tool"),
    ("Edit", 'django/forms/fields.py',                                   False, "edit"),
]
fails = 0
for tool, arg, want, label in CASES:
    got = mod._locates_code(tool, arg)
    ok = got == want; fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label:34} want={str(want):5} got={got}")

def case(label, traj, want_used):
    global fails
    r = mod.detect_agentic_exploration(traj)
    ok = r["used"] == want_used; fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label:34} used={r['used']} attempted={r['attempted']}")

case("clean run", [{"tool": "Bash", "arg": "cat django/db/models/sql/query.py"}], False)
case("grep the repo", [{"tool": "Bash", "arg": 'grep -n "def build_where" django/db/models/sql/query.py'}], True)
case("blocked grep is not a violation",
     [{"tool": "Bash", "arg": 'grep -r "x" django/', "blocked": True}], False)

# Repository text must not be mistaken for an enforcement block. Django source
# contains strings like "is not allowed", and `grep -r` prints "Permission denied"
# for unreadable paths; both previously masked a real violation.
s2 = "\n".join(json.dumps(e) for e in [
    {"message": {"content": [{"type": "tool_use", "id": "b1", "name": "Bash",
                              "input": {"command": 'grep -rn "upload_to" django/'}}]}},
    {"message": {"content": [{"type": "tool_result", "tool_use_id": "b1",
                              "content": "fields.py:88: raise ValueError('this file type is not allowed')"}]}},
])
t2 = mod.extract_trajectory(s2)
ok = not t2[0].get("blocked") and mod.detect_agentic_exploration(t2)["used"] is True
fails += not ok
print(f"{'PASS' if ok else 'FAIL'}  {'repo text w/ \"not allowed\"':34} not treated as blocked")

print(f"\n{fails} failures")
sys.exit(1 if fails else 0)
