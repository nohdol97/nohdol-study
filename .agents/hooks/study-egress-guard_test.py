#!/usr/bin/env python3
"""study-egress-guard 회귀 테스트.

실행: python3 .agents/hooks/study-egress-guard_test.py

이 훅의 위험은 양쪽에 있다. 조용히 통과시키면 노트가 외부 런타임으로 나가고,
과하게 막으면 공개 데이터 실습이 불가능해진다. 그래서 막아야 할 셀과 통과해야
할 셀을 같은 무게로 고정한다. 특히 2026-08-01 WM-811K 재현에서 실제로 돌린
셀들이 전부 통과해야 한다 — 그 셀들에는 공개 데이터셋에서 실측한 수치가 상수로
들어 있고, 그것은 vault 자료가 아니다.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

NOTE_BODY = "\n".join(
    [
        "---",
        "type: article",
        "status: developing",
        "created: 2026-08-01",
        "updated: 2026-08-01",
        "related:",
        '  - "[[반도체 P&T AX 마스터 인덱스]]"',
        "sources: []",
        "verification: primary-confirmed",
        "checked: 2026-08-01",
        "---",
        "",
        "# P&T 29 실습 05 WM-811K 실데이터 분류와 불균형 처리",
    ]
)

# 2026-08-01에 실제로 Colab에서 돌린 셀. 공개 데이터셋 실측값이 상수로 들어 있다.
REAL_CELL = '''import pandas as pd, numpy as np
df = pd.read_pickle("/content/wm811k/MIR-WM811K/Python/WM811K.pkl")
lab = df[df["label"].map(lambda x: isinstance(x, str))].copy()
REFERENCE = {"none": 147431, "Edge-Ring": 9680, "Edge-Loc": 5189, "Center": 4294,
             "Loc": 3593, "Scratch": 1193, "Random": 866, "Donut": 555, "Near-full": 149}
assert len(df) == 811457 and len(lab) == 172950
grid = [[1, 2], [3, 4]]
print(grid, REFERENCE["none"] / REFERENCE["Near-full"])
'''

failures = []


def check(name, got, want):
    if got == want:
        print("  ok   %s" % name)
        return
    failures.append(name)
    print("  FAIL %s\n       got=%r\n       want=%r" % (name, got, want))


def build_root():
    """훅이 실제 배치에서 보는 모양의 임시 루트. vault 심볼릭 링크가 핵심이다."""
    base = os.path.realpath(tempfile.mkdtemp(prefix="study-egress-guard."))
    root = os.path.join(base, "harness")
    os.makedirs(os.path.join(root, ".agents", "hooks"))
    os.makedirs(os.path.join(base, "Obsidian Vault", "wiki"))
    os.symlink(os.path.join(base, "Obsidian Vault"), os.path.join(root, "vault"))
    shutil.copy(
        os.path.join(HERE, "study-egress-guard.py"),
        os.path.join(root, ".agents", "hooks", "study-egress-guard.py"),
    )
    return base, root


def run(root, payload):
    """훅을 돌려 차단 여부만 돌려준다."""
    proc = subprocess.run(
        [sys.executable, os.path.join(root, ".agents", "hooks", "study-egress-guard.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        failures.append("hook exited %d: %s" % (proc.returncode, proc.stderr))
        return None
    out = proc.stdout.strip()
    if not out:
        return False
    decoded = json.loads(out)
    return decoded.get("decision") in ("deny", "block")


def claude(tool, args):
    return {"tool_name": tool, "tool_input": args}


def main():
    base, root = build_root()
    kroot = os.path.join(base, "Obsidian Vault")
    try:
        print("차단해야 하는 것")
        check(
            "노트 본문을 코드 셀에 넣는다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": NOTE_BODY, "cellIndex": 1})),
            True,
        )
        check(
            "노트 본문을 텍스트 셀에 넣는다",
            run(root, claude("mcp__colab-mcp__add_text_cell", {"content": NOTE_BODY})),
            True,
        )
        check(
            "update_cell로 우회한다",
            run(root, claude("mcp__colab-mcp__update_cell", {"cellId": "x", "content": NOTE_BODY})),
            True,
        )
        check(
            "지식 루트 절대 경로가 섞인다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": 'open("%s/wiki/a.md")' % kroot})),
            True,
        )
        check(
            "지식 루트 디렉터리 이름이 섞인다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": '# from Obsidian Vault'})),
            True,
        )
        check(
            "vault 상대 경로가 섞인다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": 'p = "vault/wiki/note.md"'})),
            True,
        )
        check(
            "위키링크 하나만 섞여도 막는다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": "# 근거: [[P&T 26 실습 02]]"})),
            True,
        )
        check(
            "중첩된 인자 안쪽에 숨어도 막는다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"a": {"b": ["ok", NOTE_BODY]}})),
            True,
        )

        print("통과해야 하는 것")
        check(
            "실제로 돌린 공개 데이터 셀 — 공개 실측 상수는 vault 자료가 아니다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": REAL_CELL, "cellIndex": 3})),
            False,
        )
        check(
            "중첩 리스트 [[1, 2]]를 위키링크로 오인하지 않는다",
            run(root, claude("mcp__colab-mcp__add_code_cell", {"code": "m = [[1, 2], [3, 4]]"})),
            False,
        )
        check(
            "공개 데이터셋 URL과 인용",
            run(
                root,
                claude(
                    "mcp__colab-mcp__add_code_cell",
                    {"code": '# http://mirlab.org/dataSet/public/MIR-WM811K.zip\n# Wu et al., 2015'},
                ),
            ),
            False,
        )
        check(
            "셀을 읽기만 하는 도구는 검사 대상이 아니다",
            run(root, claude("mcp__colab-mcp__get_cells", {"includeOutputs": True})),
            False,
        )
        check(
            "colab이 아닌 도구는 건드리지 않는다",
            run(root, claude("Write", {"file_path": "/x/a.md", "content": NOTE_BODY})),
            False,
        )
        check(
            "빈 페이로드에 죽지 않는다",
            run(root, {}),
            False,
        )

        print("Antigravity 방언")
        check(
            "toolCall 모양에서도 막는다",
            run(root, {"toolCall": {"name": "mcp__colab-mcp__add_code_cell", "args": {"code": NOTE_BODY}}}),
            True,
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if failures:
        print("\n%d개 실패: %s" % (len(failures), ", ".join(failures)))
        return 1
    print("\n전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
