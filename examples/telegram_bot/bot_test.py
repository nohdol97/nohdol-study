#!/usr/bin/env python3
"""텔레그램 봇 회귀 테스트.

실행: python3 examples/telegram_bot/bot_test.py
      (telegram 패키지가 필요하므로 봇 venv의 python으로 돌린다)

네트워크도 텔레그램 API도 쓰지 않는다. 토큰이 로그로 새는 경로와 하네스 루트
탐색만 확인한다 — 둘 다 실패해도 조용해서 눈으로는 알아채기 어려운 것들이다.
"""

import ast
import importlib.util
import io
import logging
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE_TOKEN = "8967314266:AAERNu9SQjv-TESTTOKEN-DoNotUse123456789"
failures = []


def check(name, got, want):
    if got == want:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name}\n     기대: {want!r}\n     실제: {got!r}")
        failures.append(name)


def load_module():
    os.environ["TELEGRAM_BOT_TOKEN"] = FAKE_TOKEN
    spec = importlib.util.spec_from_file_location(
        "bot_under_test", os.path.join(HERE, "bot.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    try:
        m = load_module()
    except ImportError as e:
        print(f"의존성이 없어 건너뜁니다: {e}")
        print("bot tests: SKIP")
        return

    print("토큰 유출 차단")

    # httpx는 요청 URL을 INFO로 남기고, 텔레그램은 토큰을 URL 경로에 담는다.
    check("httpx 로거가 INFO를 남기지 않는다",
          logging.getLogger("httpx").level >= logging.WARNING, True)

    # 레벨을 넘어 들어온 기록도 가려져야 한다.
    redactor = m.RedactToken()

    record = logging.LogRecord(
        "httpx", logging.WARNING, __file__, 1,
        f"HTTP Request: POST https://api.telegram.org/bot{FAKE_TOKEN}/getUpdates",
        None, None)
    redactor.filter(record)
    check("메시지 속 토큰이 가려진다", FAKE_TOKEN in record.msg, False)
    check("가린 자리가 표시된다", "<TOKEN>" in record.msg, True)

    record = logging.LogRecord(
        "x", logging.ERROR, __file__, 1, "failed: %s",
        (f"https://api.telegram.org/bot{FAKE_TOKEN}/sendMessage",), None)
    redactor.filter(record)
    check("포맷 인자 속 토큰도 가려진다", FAKE_TOKEN in record.args[0], False)

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "count %d", (5,), None)
    redactor.filter(record)
    check("문자열이 아닌 인자는 건드리지 않는다", record.args, (5,))

    # 실제 핸들러를 거쳐 나가는 경로 전체를 확인한다.
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(m.RedactToken())
    probe = logging.getLogger("token_probe")
    probe.addHandler(handler)
    probe.setLevel(logging.INFO)
    probe.info("url=https://api.telegram.org/bot%s/getMe", FAKE_TOKEN)
    check("핸들러를 통과한 출력에 토큰이 없다", FAKE_TOKEN in stream.getvalue(), False)

    print("\n하네스 루트 탐색")
    workdir = tempfile.mkdtemp(prefix="bot-test-")
    try:
        # 설치 경로를 코드에 적지 않고 vault 심링크로 찾는다.
        nested = os.path.join(workdir, "examples", "telegram_bot")
        os.makedirs(nested)
        os.makedirs(os.path.join(workdir, "knowledge"))
        os.symlink(os.path.join(workdir, "knowledge"),
                   os.path.join(workdir, "vault"))

        def find_from(start):
            path = os.path.abspath(start)
            for _ in range(5):
                path = os.path.dirname(path)
                if os.path.islink(os.path.join(path, "vault")):
                    return path
            return ""

        check("vault 심링크를 가진 루트를 찾는다",
              find_from(os.path.join(nested, "bot.py")), workdir)
        check("심링크가 없으면 빈 값을 준다",
              find_from(os.path.join(tempfile.gettempdir(), "nowhere", "bot.py")), "")
        check("실제 배치에서도 루트를 찾는다",
              os.path.isdir(m.find_study_root()), True)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("\n표면 표시")
    # 이 봇은 승인 프롬프트를 끈 채로 CLI를 띄우므로, PreToolUse 가드가 유일한
    # 게이트다. 표시가 빠지면 가드가 통째로 잠들고 증상은 아무 데도 안 보인다.
    # 주석이나 문서 문구로는 통과할 수 없도록 실제 호출 인자를 본다.
    with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    spawn_env = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "create_subprocess_exec":
            for keyword in node.keywords:
                if keyword.arg == "env":
                    spawn_env = keyword.value
    check("CLI 실행에 env를 넘긴다", spawn_env is not None, True)
    check("환경을 손대지 않고 그대로 넘기지 않는다", isinstance(spawn_env, ast.Name), True)

    marks = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Subscript)
            and getattr(target.slice, "value", None) == "STUDY_SURFACE"
            for target in node.targets
        )
    ]
    check("표면을 telegram으로 표시한다", [node.value.value for node in marks], ["telegram"])
    check(
        "표시한 환경을 그대로 CLI에 넘긴다",
        getattr(spawn_env, "id", None),
        marks[0].targets[0].value.id if marks else None,
    )

    print()
    if failures:
        print(f"bot tests: FAIL ({len(failures)}건) — {', '.join(failures)}")
        sys.exit(1)
    print("bot tests: PASS")


if __name__ == "__main__":
    main()
