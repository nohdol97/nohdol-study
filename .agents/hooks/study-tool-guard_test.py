#!/usr/bin/env python3
"""study-tool-guard 회귀 테스트.

실행: python3 .agents/hooks/study-tool-guard_test.py

훅은 승인 프롬프트가 없는 표면에서 유일한 게이트다. 조용히 통과시키는 실패가
가장 위험하므로, 막아야 할 호출과 막으면 안 되는 호출을 양쪽 다 고정한다.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GOOD_NOTE = "\n".join(
    [
        "---",
        "type: concept",
        "status: seed",
        "created: 2026-07-26",
        "updated: 2026-07-26",
        "related:",
        '  - "[[다른 노트]]"',
        "sources:",
        '  - "https://example.com/source"',
        "verification: source-backed",
        "checked: 2026-07-26",
        "---",
        "",
        "# 어떤 개념",
        "",
        "## 핵심",
        "",
        "설명.",
        "",
    ]
)

failures = []


def check(name, got, want):
    if got == want:
        print("  ok   %s" % name)
        return
    failures.append(name)
    print("  FAIL %s\n       got=%r\n       want=%r" % (name, got, want))


def build_root():
    """훅이 실제 배치에서 보는 것과 같은 모양의 임시 루트를 만든다.

    임시 루트를 그냥 `TMPDIR` 아래 두면 허용 목록의 임시 디렉터리가 저장소를
    통째로 삼켜 경로 검사가 사라진다. 실제 배치에서 하네스는 임시 디렉터리 밖에
    있으므로, 훅에 넘길 `TMPDIR`을 형제 디렉터리로 갈라 같은 관계를 만든다.
    """
    base = os.path.realpath(tempfile.mkdtemp(prefix="study-tool-guard."))
    root = os.path.join(base, "harness")
    os.makedirs(os.path.join(root, ".agents", "hooks"))
    os.makedirs(os.path.join(root, "knowledge", "wiki"))
    os.makedirs(os.path.join(root, "_workspace"))
    os.symlink(os.path.join(root, "knowledge"), os.path.join(root, "vault"))
    os.makedirs(os.path.join(base, "tmp"))
    shutil.copy(
        os.path.join(HERE, "study-tool-guard.py"),
        os.path.join(root, ".agents", "hooks", "study-tool-guard.py"),
    )
    return root


def scratch_dir(root):
    return os.path.join(os.path.dirname(root), "tmp")


def run(root, payload, surface="telegram"):
    """훅을 실제로 실행하고 (차단 여부, 사유)를 돌려준다."""
    env = dict(os.environ)
    env["TMPDIR"] = scratch_dir(root)
    if surface is None:
        env.pop("STUDY_SURFACE", None)
    else:
        env["STUDY_SURFACE"] = surface
    payload.setdefault("cwd", root)
    result = subprocess.run(
        [sys.executable, os.path.join(root, ".agents", "hooks", "study-tool-guard.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        return "crashed", result.stderr.strip()
    if not result.stdout.strip():
        # 두 CLI 모두 무출력을 "관여하지 않음"으로 읽는다. Antigravity에서는
        # 실제 세션으로 확인했다 — 무출력 훅을 건 채 파일 쓰기가 그대로 됐다.
        return "allow", ""
    parsed = json.loads(result.stdout)
    if "hookSpecificOutput" in parsed:
        block = parsed["hookSpecificOutput"]
        return block["permissionDecision"], block["permissionDecisionReason"]
    return parsed["decision"], parsed.get("reason", "")


def raw_output(root, payload):
    """차단 응답의 원문 JSON. CLI별 형식이 섞이지 않았는지 본다."""
    env = dict(os.environ, STUDY_SURFACE="telegram", TMPDIR=scratch_dir(root))
    payload.setdefault("cwd", root)
    result = subprocess.run(
        [sys.executable, os.path.join(root, ".agents", "hooks", "study-tool-guard.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def agy(root, name, args):
    """Antigravity 계약(protojson camelCase)으로 훅을 부른다."""
    return run(root, {"toolCall": {"name": name, "args": args}})


def write(root, path, content=GOOD_NOTE, tool="Write"):
    payload = {"tool_name": tool, "tool_input": {"file_path": path}}
    if content is not None and tool == "Write":
        payload["tool_input"]["content"] = content
    return run(root, payload)


def bash(root, command, surface="telegram"):
    return run(root, {"tool_name": "Bash", "tool_input": {"command": command}}, surface)


def main():
    root = build_root()
    vault = os.path.join(root, "vault")
    try:
        print("표면 구분")
        # 프롬프트가 살아 있는 표면에서는 게이트가 이미 있으므로 관여하지 않는다.
        check(
            "표면 표시가 없으면 vault 밖 쓰기도 통과시킨다",
            run(
                root,
                {"tool_name": "Write", "tool_input": {"file_path": os.path.join(root, "AGENTS.md"), "content": "x"}},
                surface=None,
            )[0],
            "allow",
        )
        check(
            "다른 표면 이름도 관여 대상이 아니다",
            bash(root, "find ~ -maxdepth 3 -name '*.md'", surface="terminal")[0],
            "allow",
        )

        print("쓰기 경로")
        check("vault 안 노트는 통과한다", write(root, os.path.join(vault, "wiki", "어떤 개념.md"))[0], "allow")
        check(
            "하네스 저장소 쓰기는 차단한다",
            write(root, os.path.join(root, "AGENTS.md"), content=None, tool="Edit")[0],
            "deny",
        )
        check(
            "홈 디렉터리 쓰기는 차단한다",
            write(root, os.path.expanduser("~/notes.md"), content=None, tool="Edit")[0],
            "deny",
        )
        check(
            "_workspace 는 제안을 두는 곳이라 허용한다",
            write(root, os.path.join(root, "_workspace", "proposal.md"), content=None, tool="Edit")[0],
            "allow",
        )
        check(
            "임시 디렉터리는 허용한다",
            write(root, os.path.join(scratch_dir(root), "scratch.txt"), content=None, tool="Edit")[0],
            "allow",
        )
        # vault 는 심링크다. 실경로로 정규화하지 않으면 경로 검사가 통째로 빗나간다.
        check(
            "심링크를 지나 실경로로 판정한다",
            write(root, os.path.join(root, "knowledge", "wiki", "어떤 개념.md"))[0],
            "allow",
        )
        check(
            "상대 경로도 cwd 기준으로 판정한다",
            write(root, "vault/wiki/어떤 개념.md")[0],
            "allow",
        )
        check("상대 경로로 저장소를 건드리면 차단한다", write(root, "AGENTS.md", content=None, tool="Edit")[0], "deny")

        print("노트 계약")
        missing = GOOD_NOTE.replace("verification: source-backed\n", "")
        decision, reason = write(root, os.path.join(vault, "wiki", "어떤 개념.md"), content=missing)
        check("필수 필드가 빠지면 차단한다", decision, "deny")
        check("사유가 빠진 필드를 지목한다", "verification" in reason, True)
        check("사유가 note-writer 로 안내한다", "note-writer" in reason, True)

        check(
            "프론트매터가 아예 없으면 차단한다",
            write(root, os.path.join(vault, "wiki", "어떤 개념.md"), content="# 어떤 개념\n\n본문.\n")[0],
            "deny",
        )
        check(
            "status 값이 계약 밖이면 차단한다",
            write(
                root,
                os.path.join(vault, "wiki", "어떤 개념.md"),
                content=GOOD_NOTE.replace("status: seed", "status: draft"),
            )[0],
            "deny",
        )
        check(
            "verification 값이 계약 밖이면 차단한다",
            write(
                root,
                os.path.join(vault, "wiki", "어떤 개념.md"),
                content=GOOD_NOTE.replace("verification: source-backed", "verification: ok"),
            )[0],
            "deny",
        )
        check(
            "날짜 형식이 어긋나면 차단한다",
            write(
                root,
                os.path.join(vault, "wiki", "어떤 개념.md"),
                content=GOOD_NOTE.replace("checked: 2026-07-26", "checked: 2026/07/26"),
            )[0],
            "deny",
        )
        # H1 과 파일명이 어긋나면 위키링크가 노트를 못 찾는다.
        check(
            "H1 이 파일명과 다르면 차단한다",
            write(root, os.path.join(vault, "wiki", "다른 이름.md"), content=GOOD_NOTE)[0],
            "deny",
        )
        check(
            "wiki 밖 vault 파일에는 노트 계약을 적용하지 않는다",
            write(root, os.path.join(vault, "log.md"), content="# log\n")[0],
            "allow",
        )
        # Edit 은 이미 이 게이트를 통과한 노트의 일부만 바꾼다.
        check(
            "Edit 은 경로만 본다",
            write(root, os.path.join(vault, "wiki", "어떤 개념.md"), content=None, tool="Edit")[0],
            "allow",
        )

        print("Bash — 홈 스캔과 보호 경로")
        check("홈 전체 스캔을 차단한다", bash(root, "find ~ -maxdepth 3 -name '*.md'")[0], "deny")
        check("$HOME 형태도 차단한다", bash(root, "find $HOME -name vault")[0], "deny")
        check(
            "절대 경로 홈도 차단한다",
            bash(root, "find /Users/%s -maxdepth 2" % os.path.basename(os.path.expanduser("~")))[0],
            "deny",
        )
        check("파이프 뒤에 숨겨도 차단한다", bash(root, "echo hi | true; du -sh ~")[0], "deny")
        check("미리 알림 폴더 접근을 차단한다", bash(root, "ls ~/Library/Reminders")[0], "deny")
        check("캘린더 폴더 접근을 차단한다", bash(root, "ls -la ~/Library/Calendars")[0], "deny")
        check(
            "AppleScript 로 개인 앱을 여는 것도 차단한다",
            bash(root, 'osascript -e \'tell application "Reminders" to get name of lists\'')[0],
            "deny",
        )
        # 홈 아래 특정 하위 경로 탐색은 스윕이 아니다.
        check("홈 하위 경로 탐색은 통과한다", bash(root, "find ~/Documents/notes -name '*.md'")[0], "allow")
        check("vault 안 탐색은 통과한다", bash(root, "find vault/wiki -name '*.md'")[0], "allow")

        print("Bash — 쓰기 우회")
        check(
            "vault 밖 리다이렉션을 차단한다",
            bash(root, "echo hi > %s" % os.path.join(root, "AGENTS.md"))[0],
            "deny",
        )
        check(
            "tee 우회도 차단한다",
            bash(root, "echo hi | tee -a %s" % os.path.expanduser("~/notes.md"))[0],
            "deny",
        )
        check("vault 안 리다이렉션은 통과한다", bash(root, "echo hi > vault/wiki/tmp.md")[0], "allow")
        # 아래 셋은 오탐이 나기 쉬운 형태다. 하나라도 막히면 봇이 아무것도 못 한다.
        check("stderr 버리기는 통과한다", bash(root, "rg foo vault/ 2>/dev/null")[0], "allow")
        check("파일 서술자 병합은 통과한다", bash(root, "make build > /dev/null 2>&1")[0], "allow")
        check("평범한 읽기 명령은 통과한다", bash(root, "git status --short")[0], "allow")

        print("Antigravity 계약")
        # 텔레그램 봇이 실제로 띄우는 CLI는 Claude Code가 아니라 agy다.
        # 도구 이름도 인자 키도 전부 다르므로 같은 규칙을 그 형식으로도 고정한다.
        check(
            "write_to_file 이 vault 안이면 통과한다",
            agy(
                root,
                "write_to_file",
                {"TargetFile": os.path.join(vault, "wiki", "어떤 개념.md"), "CodeContent": GOOD_NOTE},
            )[0],
            "allow",
        )
        check(
            "write_to_file 이 홈으로 향하면 차단한다",
            agy(
                root,
                "write_to_file",
                {"TargetFile": os.path.expanduser("~/notes.md"), "CodeContent": "probe"},
            )[0],
            "deny",
        )
        check(
            "write_to_file 도 노트 계약을 검사한다",
            agy(
                root,
                "write_to_file",
                {"TargetFile": os.path.join(vault, "wiki", "어떤 개념.md"), "CodeContent": "# 어떤 개념\n"},
            )[0],
            "deny",
        )
        check(
            "file_change 는 경로만 본다",
            agy(root, "file_change", {"TargetFile": os.path.join(vault, "wiki", "어떤 개념.md")})[0],
            "allow",
        )
        check(
            "delete_file 도 vault 밖이면 차단한다",
            agy(root, "delete_file", {"TargetFile": os.path.join(root, "AGENTS.md")})[0],
            "deny",
        )
        check("run_command 로 홈을 훑으면 차단한다", agy(root, "run_command", {"CommandLine": "find ~ -name '*.md'"})[0], "deny")
        check("run_command 의 평범한 명령은 통과한다", agy(root, "run_command", {"CommandLine": "git status"})[0], "allow")
        # 셸의 cwd 는 명령 인자로 따로 온다. 이걸 놓치면 상대 경로 판정이 어긋난다.
        check(
            "run_command 의 Cwd 기준으로 상대 경로를 푼다",
            agy(root, "run_command", {"CommandLine": "echo x > notes.md", "Cwd": os.path.expanduser("~")})[0],
            "deny",
        )
        check(
            "읽기 전용 도구는 관여하지 않는다",
            agy(root, "view_file", {"AbsolutePath": os.path.expanduser("~/anything.md")})[0],
            "allow",
        )
        # agy 는 allow/deny/ask/force_ask 만 안다. "block" 을 주면 해석되지 않는다.
        denied = raw_output(
            root,
            {"toolCall": {"name": "write_to_file", "args": {"TargetFile": os.path.expanduser("~/x.md"), "CodeContent": "x"}}},
        )
        check("agy 차단 응답의 decision 은 deny 다", denied.get("decision"), "deny")
        check("agy 응답에 Claude 전용 필드를 섞지 않는다", "hookSpecificOutput" in denied, False)
        claude_denied = raw_output(
            root, {"tool_name": "Write", "tool_input": {"file_path": os.path.expanduser("~/x.md"), "content": "x"}}
        )
        check(
            "Claude 차단 응답은 permissionDecision 을 쓴다",
            claude_denied.get("hookSpecificOutput", {}).get("permissionDecision"),
            "deny",
        )

        print("입력 방어")
        result = subprocess.run(
            [sys.executable, os.path.join(root, ".agents", "hooks", "study-tool-guard.py")],
            input="not json at all",
            capture_output=True,
            text=True,
            env=dict(os.environ, STUDY_SURFACE="telegram"),
        )
        check("깨진 입력에 죽지 않는다", result.returncode, 0)
        check("깨진 입력을 차단으로 바꾸지 않는다", result.stdout.strip(), "")
        check("모르는 도구는 통과시킨다", run(root, {"tool_name": "Grep", "tool_input": {"pattern": "x"}})[0], "allow")
    finally:
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)

    print()
    if failures:
        print("tool guard tests: FAIL (%d건) — %s" % (len(failures), ", ".join(failures)))
        sys.exit(1)
    print("tool guard tests: PASS")


if __name__ == "__main__":
    main()
