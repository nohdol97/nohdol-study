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

        # 노트가 다른 폴더로 옮겨졌는데 'path'가 낡았을 때. 그대로 만들면 빈
        # 대기열이 하나 더 생기고 오늘 수집분만 거기 쌓이는데, 누적본은 옮겨 간
        # 자리에 그대로 있어 아무것도 실패하지 않는다 - 그래서 멈춰야 한다.
        print("\n옮겨진 노트")
        moved_dir = os.path.join(m.WIKI_ROOT, "Moved")
        os.makedirs(moved_dir, exist_ok=True)
        with open(os.path.join(moved_dir, "Roaming.md"), "w", encoding="utf-8") as f:
            f.write("---\ntype: moc\n---\n\n# Roaming\n\n## 2026-07\n\n- 기존 누적분\n")
        roaming = dict(source, path="Test/Roaming.md", window_days=3650,
                       rss=rss(("Fresh", "https://e.test/r",
                                "Thu, 23 Jul 2026 00:00:00 +0000")))
        m.scrape_feed_source('roaming', roaming)
        check("낡은 경로에 새 대기열을 만들지 않는다",
              os.path.exists(os.path.join(m.WIKI_ROOT, "Test", "Roaming.md")), False)
        check("옮겨 간 노트를 건드리지도 않는다",
              "src:roaming:" in open(os.path.join(moved_dir, "Roaming.md"),
                                     encoding="utf-8").read(), False)
        check("경로가 맞으면 평소대로 만든다",
              (m.scrape_feed_source('roaming', dict(roaming, path="Moved/Fine.md")),
               os.path.exists(os.path.join(moved_dir, "Fine.md")))[1], True)

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

        # 월 인덱스 — 폴더에서 다시 만들어 고아 노트를 막는다.
        print("\nrefresh_month_index")
        import datetime
        month_dir = os.path.join(m.DAILY_DIR, "2026.7")
        os.makedirs(month_dir, exist_ok=True)
        for day in ("2026-07-24", "2026-07-25"):
            with open(os.path.join(month_dir, f"{day}.md"), "w",
                      encoding="utf-8") as f:
                f.write(f"# {day}\n")
        index_path = os.path.join(m.DAILY_DIR, "2026.7 인덱스.md")
        # 하루가 빠진 인덱스를 만들어 둔다. 실제로 이런 상태였다.
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("---\ncreated: 2026-07-01\nupdated: 2026-07-01\n---\n\n"
                    "# 📰 GeekNews 2026.7 아카이브 인덱스\n\n- [[2026-07-24]]\n")

        m.refresh_month_index(datetime.datetime(2026, 7, 26))
        index = open(index_path, encoding="utf-8").read()
        check("빠졌던 날짜가 메워진다", "[[2026-07-25]]" in index, True)
        check("기존 날짜도 남는다", "[[2026-07-24]]" in index, True)
        check("개수 안내가 실제와 맞는다", "리포트 2개의" in index, True)
        check("created는 보존된다", "created: 2026-07-01" in index, True)
        check("허브를 related로 가리킨다",
              '- "[[GeekNews 큐레이션 허브]]"' in index, True)

        # 층이 갈리는 기준은 "사람의 판단이 들어갔는가"다. 자동 생성물(캡처·월 인덱스)은
        # raw, 사람이 정한 분류(주제 문서)만 wiki. 한쪽으로 몰리면 원자 노트를 세는
        # 지표가 수집량에 휩쓸리므로 경로로 못박는다.
        check("일일 캡처는 raw/geeknews 아래에 쌓인다",
              m.note_path(datetime.datetime(2026, 7, 25)).startswith(m.DAILY_DIR), True)
        check("월 인덱스도 raw/geeknews에 있다",
              index_path.startswith(m.DAILY_DIR), True)
        check("raw 산출물은 wiki를 건드리지 않는다",
              index_path.startswith(m.WIKI_ROOT), False)
        check("주제 문서만 wiki/GeekNews에 남는다",
              m.TOPIC_DIR == os.path.join(m.WIKI_ROOT, "GeekNews"), True)
        check("주제 문서는 하위 디렉터리를 두지 않는다",
              os.path.basename(m.TOPIC_DIR), "GeekNews")

        # 두 번째 호출은 아무것도 바꾸지 않아야 한다. 매 실행 mtime을 건드리면
        # 파일 시각에 기대는 도구가 헛돌고 클라우드 sync도 매번 올린다.
        before = os.stat(index_path).st_mtime_ns
        m.refresh_month_index(datetime.datetime(2026, 7, 26))
        check("내용이 같으면 다시 쓰지 않는다",
              os.stat(index_path).st_mtime_ns, before)

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
