#!/usr/bin/env python3
"""피드 스크래퍼 회귀 테스트.

실행: python3 examples/feed_scraper/scrape_test.py

네트워크를 쓰지 않는다. feedparser는 URL뿐 아니라 문자열도 파싱하므로, 각
테스트가 필요한 RSS를 직접 지어내 넘긴다. 그래야 피드 쪽 사정과 무관하게
같은 결과가 나온다.
"""

import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
failures = []


def check(name, got, want):
    if got == want:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name}\n     기대: {want!r}\n     실제: {got!r}")
        failures.append(name)


def rss(*items):
    """항목 목록으로 최소한의 RSS 문서를 만든다. (제목, 링크, RFC822 날짜)"""
    body = "".join(
        f"<item><title>{t}</title><link>{l}</link><pubDate>{d}</pubDate></item>"
        for t, l, d in items
    )
    return f"<?xml version='1.0'?><rss version='2.0'><channel>{body}</channel></rss>"


def load_module(workdir):
    """임시 설정을 주입해 scrape.py를 불러온다.

    모듈 최상단이 설정을 읽고 하네스 루트를 찾으므로, 그 둘을 먼저 갖춰 둔다.
    """
    config = os.path.join(workdir, "sources.local.toml")
    with open(config, "w", encoding="utf-8") as f:
        f.write(f'enabled = []\nstudy_root = "{workdir}"\n')
    os.makedirs(os.path.join(workdir, "knowledge", "wiki"), exist_ok=True)
    os.symlink(os.path.join(workdir, "knowledge"), os.path.join(workdir, "vault"))

    os.environ["FEED_SCRAPER_CONFIG"] = config
    spec = importlib.util.spec_from_file_location(
        "scrape_under_test", os.path.join(HERE, "scrape.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    workdir = tempfile.mkdtemp(prefix="feed-scraper-test-")
    try:
        m = load_module(workdir)

        # 제목 정리 — 링크 텍스트를 깨뜨리는 세 가지를 막는다.
        print("clean_title")
        check("날것의 태그를 엔티티로 되돌린다",
              m.clean_title("What should go in the <license> tag?"),
              "What should go in the &lt;license> tag?")
        check("닫는 태그도 함께 무력화한다",
              m.clean_title("<script>x</script>"),
              "&lt;script>x&lt;/script>")
        check("대괄호를 이스케이프한다(위키링크 오인 방지)",
              m.clean_title("[Nav2] Benchmark"), "\\[Nav2\\] Benchmark")
        check("HTML 엔티티는 원문으로 되돌린다",
              m.clean_title("Say &quot;hi&quot;"), 'Say "hi"')

        # 수집 — 목록 문서 한 개에 월별로 쌓인다.
        print("\nscrape_feed_source")
        source = {
            'name': "Test Feed",
            'pipeline': 'feed',
            'rss': rss(
                ("Old June post", "https://e.test/a", "Mon, 15 Jun 2026 00:00:00 +0000"),
                ("New July post", "https://e.test/b", "Wed, 22 Jul 2026 00:00:00 +0000"),
            ),
            'path': "Test/Test Feed.md",
            'tags': ["test", "feed"],
            'hub': "테스트 허브",
            'window_days': 3650,
        }
        m.scrape_feed_source('test', source)
        path = os.path.join(m.WIKI_ROOT, "Test", "Test Feed.md")
        text = open(path, encoding="utf-8").read()
        check("두 항목이 기록된다", text.count("<!-- src:test:"), 2)
        check("월 섹션은 최신이 위",
              [l for l in text.split("\n") if l.startswith("## ")],
              ["## 2026-07", "## 2026-06"])
        check("허브를 related로 가리킨다", '- "[[테스트 허브]]"' in text, True)
        check("요약 없이 제목과 링크만 남는다",
              "[New July post](https://e.test/b)" in text, True)

        # 같은 피드를 다시 돌려도 늘지 않아야 한다. 하루 여러 번 실행되기 때문이다.
        m.scrape_feed_source('test', source)
        again = open(path, encoding="utf-8").read()
        check("재실행해도 중복되지 않는다", again.count("<!-- src:test:"), 2)

        # 새 항목만 늘어난다.
        source['rss'] = rss(
            ("New July post", "https://e.test/b", "Wed, 22 Jul 2026 00:00:00 +0000"),
            ("Newest post", "https://e.test/c", "Thu, 23 Jul 2026 00:00:00 +0000"),
        )
        m.scrape_feed_source('test', source)
        grown = open(path, encoding="utf-8").read()
        check("새 항목만 더해진다", grown.count("<!-- src:test:"), 3)

        # 창 밖의 글은 받지 않는다.
        print("\nwindow_days")
        narrow = dict(source, path="Test/Narrow.md", window_days=1,
                      rss=rss(("Ancient", "https://e.test/z",
                               "Mon, 15 Jun 2020 00:00:00 +0000")))
        m.scrape_feed_source('narrow', narrow)
        check("창보다 오래된 글은 문서를 만들지 않는다",
              os.path.exists(os.path.join(m.WIKI_ROOT, "Test", "Narrow.md")), False)

        # 주제 전용이 아닌 피드는 제목으로 거른다.
        print("\ntitle_filter")
        filtered = dict(source, path="Test/Filtered.md", window_days=3650,
                        title_filter=["robot", "lerobot"],
                        rss=rss(
                            ("A new LLM tokenizer", "https://e.test/1",
                             "Wed, 22 Jul 2026 00:00:00 +0000"),
                            ("LeRobot v1.0 released", "https://e.test/2",
                             "Wed, 22 Jul 2026 00:00:00 +0000"),
                            ("Robot arm dataset", "https://e.test/3",
                             "Wed, 22 Jul 2026 00:00:00 +0000"),
                        ))
        m.scrape_feed_source('filtered', filtered)
        ftext = open(os.path.join(m.WIKI_ROOT, "Test", "Filtered.md"),
                     encoding="utf-8").read()
        check("걸리는 항목만 남는다", ftext.count("<!-- src:filtered:"), 2)
        check("관련 없는 글은 빠진다", "tokenizer" in ftext, False)
        check("대소문자를 가리지 않는다", "LeRobot v1.0" in ftext, True)

        # 카탈로그가 파이프라인이 요구하는 항목을 갖췄는지. 소스를 더할 때
        # 키를 빠뜨리면 그 소스만 조용히 죽으므로 여기서 잡는다.
        print("\nSOURCES 카탈로그")
        required = ('rss', 'path', 'tags', 'hub', 'window_days')
        for key, spec in m.SOURCES.items():
            if spec.get('pipeline') != 'feed':
                continue
            missing = [f for f in required if f not in spec]
            check(f"{key}: 필수 항목이 모두 있다", missing, [])
        paths = [s['path'] for s in m.SOURCES.values() if s.get('pipeline') == 'feed']
        check("저장 경로가 서로 겹치지 않는다", len(paths), len(set(paths)))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        os.environ.pop("FEED_SCRAPER_CONFIG", None)

    print()
    if failures:
        print(f"scrape tests: FAIL ({len(failures)}건) — {', '.join(failures)}")
        sys.exit(1)
    print("scrape tests: PASS")


if __name__ == "__main__":
    main()
