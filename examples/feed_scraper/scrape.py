"""RSS 소스를 연결된 vault로 수집한다.

두 가지 파이프라인이 있다.

- `feed`   제목과 링크만 소스별 목록 문서에 쌓는다. 본문을 읽지 않으므로 API
           호출이 없고, 소스를 몇 개 붙이든 외부 한도와 무관하다.
- `geeknews` GeekNews 전용. 투표 점수가 있어 대기 목록에 쌓아 두고 다음 날
           채점한 뒤, 기준을 통과한 글만 Gemini로 요약·분류한다.

어느 소스를 켤지는 컴퓨터마다 다르므로 이 파일이 아니라 `sources.local.toml`이
정한다. 이 파일은 카탈로그이고, 그 파일이 선택이다.

설치와 운영은 `docs/guides/feed-scraper.md`에 있다.
"""

import html
import html2text
import feedparser
import datetime
import pytz
import glob
import json
import os
import re
import sys
import tomllib
import urllib.request
import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 설정 위치. 환경 변수로 바꿀 수 있게 둔 이유는 둘이다 - 테스트가 임시 설정을
# 주입할 수 있어야 하고, 같은 코드를 다른 소스 묶음으로 시험 실행할 때도 쓴다.
CONFIG_PATH = os.environ.get("FEED_SCRAPER_CONFIG") or os.path.join(
    BASE_DIR, "sources.local.toml"
)


def load_config():
    """설치별 설정을 읽는다. 없으면 무엇을 해야 하는지 말하고 멈춘다.

    조용히 기본값으로 도는 것이 더 나빠 보일 수 있지만, 그러면 이 컴퓨터에서
    원하지 않는 소스가 vault에 쌓인다. 선택은 설치마다 다르므로 명시를 요구한다.
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"설정이 없습니다: {CONFIG_PATH}")
        print("sources.local.example.toml을 복사해 켤 소스를 고르세요.")
        sys.exit(1)
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def find_study_root():
    """`vault` 심링크를 가진 하네스 루트를 위로 올라가며 찾는다.

    설치 경로를 이 파일에 적지 않기 위해서다. 하네스는 vault를 심링크로 걸어
    두므로, 그것을 찾으면 지식 저장 위치를 설치와 무관하게 얻는다.
    """
    path = BASE_DIR
    for _ in range(5):
        path = os.path.dirname(path)
        if os.path.islink(os.path.join(path, "vault")):
            return path
    return None


CONFIG = load_config()

_root = CONFIG.get('study_root') or find_study_root()
if not _root:
    print("하네스 루트를 찾지 못했습니다. sources.local.toml에 study_root를 적으세요.")
    sys.exit(1)
WIKI_ROOT = os.path.join(_root, "vault", "wiki")

# 켤 소스. 카탈로그에 없는 키는 오타이므로 조용히 넘기지 않는다.
ENABLED = CONFIG.get('enabled', [])

# ---------------------------------------------------------
# Google Gemini API Key 설정
# .env 파일에서 불러옵니다. `geeknews` 파이프라인만 사용합니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# `gemini-flash-latest`는 최신 flash(3.6)로 해석되는데, 그 모델의 무료 티어
# 일일 한도는 실측 결과 20건이라 하루 수집분(약 12건)만으로도 60%를 쓴다.
# lite는 한도가 넉넉하고, 분류 정확도는 정답이 분명한 12건 배치에서 12/12였다.
GEMINI_MODEL = "gemini-flash-lite-latest"
# ---------------------------------------------------------

GEEKNEWS_RSS = "https://news.hada.io/rss/news"
TOPIC_URL = "https://news.hada.io/topic?id={topic_id}"
VAULT_DIR = os.path.join(WIKI_ROOT, "GeekNews")

# ---------------------------------------------------------
# 소스 카탈로그.
#
# 여기 있다고 수집되지 않는다. `sources.local.toml`의 `enabled`에 키를 적어야
# 켜진다. 카탈로그와 선택을 나눈 이유는 컴퓨터마다 관심사가 다르기 때문이다.
#
# 새 소스를 더하기 전에 두 가지를 실측한다:
#   1) published_parsed 유무 - 없으면 날짜를 적을 수 없어 건너뛴다
#   2) 피드 창(가장 오래된~최신 항목의 시간 폭) - `window_days`를 그보다
#      넉넉히 잡아야 놓치지 않는다
# 재는 방법과 탈락한 후보는 vault의 [[로봇과 피지컬 AI 정보 소스]]에 있다.
# ---------------------------------------------------------
SOURCES = {
    'geeknews': {
        'name': "GeekNews",
        'pipeline': 'geeknews',
        # 점수·요약·분류를 거치므로 Gemini API 키가 필요하다.
        'needs_api_key': True,
    },
    'ieee-robotics': {
        'name': "IEEE Spectrum Robotics",
        'pipeline': 'feed',
        'rss': "https://spectrum.ieee.org/feeds/topic/robotics.rss",
        'path': "Robotics/IEEE Spectrum Robotics.md",
        'tags': ["robotics", "physical-ai", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 실측(2026-07-26) 30건이 67일에 걸쳐 있고 일평균 0.4건. 창이 아주 넓다.
        'window_days': 14,
    },
    'the-robot-report': {
        'name': "The Robot Report",
        'pipeline': 'feed',
        'rss': "https://www.therobotreport.com/feed/",
        'path': "Robotics/The Robot Report.md",
        'tags': ["robotics", "industry", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 실측 15건이 4.1일에 걸쳐 있고 일평균 3.7건. 창이 좁으므로 14일로
        # 넉넉히 잡아 하루 한 번 실행에서도 놓치지 않게 한다.
        'window_days': 14,
    },
    'ros-discourse': {
        'name': "ROS Discourse",
        'pipeline': 'feed',
        'rss': "https://discourse.openrobotics.org/latest.rss",
        'path': "Robotics/ROS Discourse.md",
        'tags': ["robotics", "ros", "forum", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 일평균 6.7건으로 가장 활발하지만, 첫 표본 30건에서 개념 노트감이
        # 0건이었다 - 구인·밋업·안부·개별 프로젝트가 섞인다. 다른 소스는 3~5건에
        # 1건씩 나왔으므로 밀도가 확연히 낮다. 그래서 기본값을 끔으로 둔다.
        #
        # 버릴 소스는 아니다. ROS를 직접 쓰기 시작하면 여기 실무 스레드가 가장
        # 값있어지므로, 그때 `enabled`에 키를 적으면 된다.
        'window_days': 14,
    },
    'robohub': {
        'name': "Robohub",
        'pipeline': 'feed',
        'rss': "https://robohub.org/feed/",
        'path': "Robotics/Robohub.md",
        'tags': ["robotics", "research", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 연구를 일반 독자용으로 옮기는 축. arXiv cs.RO는 API로 받을 수 있지만
        # 일 34.9편이라 훑는 대기열이 아니라 질의 대상이고, 논문 자체는
        # `paper-search` 스킬이 담당한다. 여기서 필요한 것은 걸러진 연구 소식
        # 쪽이다. 실측 75건이 191일에 걸쳐 있고 일평균 0.4건.
        'window_days': 14,
    },
    'nvidia-robotics': {
        'name': "NVIDIA Robotics",
        'pipeline': 'feed',
        'rss': "https://blogs.nvidia.com/blog/category/robotics/feed/",
        'path': "Robotics/NVIDIA Robotics.md",
        'tags': ["robotics", "physical-ai", "vendor", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 피지컬 AI 스택(Isaac, GR00T) 발표처. 벤더 블로그이므로 자사 제품
        # 홍보가 섞인다 - 제목 목록으로만 쓰고 주장은 원문에서 확인할 것.
        # 실측 18건이 118일에 걸쳐 있고 일평균 0.2건.
        'window_days': 14,
    },
    'huggingface-robotics': {
        'name': "Hugging Face (로봇)",
        'pipeline': 'feed',
        'rss': "https://huggingface.co/blog/feed.xml",
        'path': "Robotics/Hugging Face 로봇.md",
        'tags': ["robotics", "physical-ai", "open-source", "feed"],
        'hub': "로봇과 피지컬 AI 정보 소스",
        # 이 피드는 로봇 전용이 아니다. 실측 831건 중 제목에 로봇 관련어가
        # 있는 것은 23건(2.8%)뿐이라 거르지 않으면 LLM·디퓨전 글이 목록을
        # 덮는다. 남는 23건은 LeRobot 릴리스와 피지컬 AI 시뮬레이션 개관처럼
        # 다른 소스에 없는 것들이라, 버리기보다 거르는 편이 낫다.
        #
        # LeRobot의 GitHub releases(연 10회)도 같은 내용을 담지만 제목이
        # `Release v0.6.0`뿐이라 무엇이 바뀌었는지 알 수 없다. 블로그 쪽이
        # 릴리스마다 설명적인 제목을 달아 주므로 이쪽만 받는다.
        'window_days': 30,
        'title_filter': [
            "robot", "lerobot", "embodied", "manipulat", "physical ai",
            "humanoid", "teleop", "so-100", "so100",
        ],
    },
}

# 일반 피드 항목의 중복 표시. GeekNews의 topic id에 해당하는 것이 없으므로
# 링크를 그대로 쓴다.
FEED_MARKER = "<!-- src:{key}:{uid} -->"

# 목록 대기소. RSS는 최근 50건·약 33시간만 담으므로 이틀 전 글은 이미 빠져 있다.
# 그래서 매 실행이 RSS에 보이는 글을 날짜별 목록에 쌓아두고, 점수는 나중에 매긴다.
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

# 이 점수 미만은 저장하지 않는다. GeekNews의 점수 분포는 HN보다 훨씬 낮아
# (최근 14일 392건 실측 중앙값 2P) 5P가 상위 약 29%, 하루 8건 정도다.
MIN_POINTS = 5

# 점수와 무관하게 받아 두는 관심어. 점수는 GeekNews 전체 투표자의 관심을 재는
# 값이라 개인 관련성과는 다르다 — 실측에서 Claude Code·Codex 운영에 관한 글이
# 5~9P 구간에 몰려 있었고, 점수만으로 자르면 가장 관련 깊은 글을 놓쳤다.
# 검사 대상은 제목뿐이다(matched_interest 참고).
INTEREST_TERMS = [
    "claude code", "claude", "anthropic", "codex", "mcp",
    "obsidian", "subagent", "서브에이전트", "에이전트", "agentic",
]

# 어제 글을 대상으로 삼는다. 처음에는 점수 숙성을 위해 이틀을 뒀지만, 실측에서
# 그 대가가 근거 없이 비쌌다 - 1~2일 경과 글의 평균이 6.5P인데 7~14일 경과 글은
# 5.8P로, 오래 둔다고 점수가 오르지 않는다. 날짜별 편차(3.5~7.8P)가 경과일 효과보다
# 훨씬 커서 하루와 이틀의 차이는 그날 글 품질의 우연에 가깝다. 그래서 뉴스를 이틀
# 묵혀 보는 비용만 남았다.
LOOKBACK_DAYS = 1

# 처리한 날짜 목록을 이 기간만 남기고 지운다.
PENDING_KEEP_DAYS = 10

REQUEST_INTERVAL = 0.7
USER_AGENT = "study-feed-scraper/1.0 (personal Obsidian archive)"

# 요약 호출 사이 대기. 2026-07-24 실행이 27건을 몰아치다 429로 중단된 기록이
# 로그에 있어 분당 요청 수를 낮춰 잡았다. 실측해 보니 더 빡빡한 것은 일일
# 한도였다 - `gemini-flash-latest`(=3.6-flash)는 무료 티어에서 하루 20건이라
# 하루 수집분만으로 60%를 썼다. 그래서 모델을 lite로 옮겼고, 이 간격은 분당
# 한도에 대한 보수적인 여유로 남긴다.
SUMMARY_INTERVAL = 7

CONTENTS = re.compile(r"<section id='topic_contents'[^>]*>(.*?)</section>", re.S)
TOPIC_ID = re.compile(r"topic\?id=(\d+)")
# 본문 안의 제목은 노트에서 글을 구분하는 `##`보다 깊어야 한다. 그러지 않으면
# 본문 소제목이 글 제목과 같은 수준으로 목차에 섞인다.
BODY_HEADING = re.compile(r"^(#{1,4})\s", re.M)

# 요약에 넘길 본문 길이 상한. GeekNews 본문은 1만 자를 넘기도 한다.
SUMMARY_INPUT_LIMIT = 4000

# 주제 문서를 둘 곳. 날짜별 파일은 원본으로 남고, 여기 문서들이 그 글을 주제별로
# 가리킨다. 분류 기준이 바뀌면 원본에서 다시 만들 수 있다.
TOPIC_DIR = os.path.join(VAULT_DIR, "주제")

# 최근 14일 10P+ 63건의 실제 분포에서 뽑은 분류다. 고정 목록인 이유는, 자유롭게
# 주제를 지어내게 하면 "LLM"과 "LLMOps"와 "언어모델"이 각각 문서를 만들기 때문이다.
# 마지막 'other'는 억지로 끼워 넣는 것을 막는 자리다.
CATEGORIES = {
    'philosophy': "엔지니어링 철학과 커리어",
    'ai-agents': "AI와 LLM 에이전트",
    'devtools': "개발 도구와 셀프호스팅",
    'business': "비즈니스와 제품 전략",
    'systems-data': "시스템과 데이터베이스",
    'frontend': "프론트엔드와 UI 디자인",
    'other': "기타 주제",
}
CATEGORY_HINTS = {
    'philosophy': "engineering philosophy, career, hiring, learning, how to work, essays on craft",
    'ai-agents': "LLM models, coding agents, agent tooling, AI ecosystem news",
    'devtools': "CLI tools, developer utilities, self-hosted software, open source releases",
    'business': "startups, product strategy, growth, pricing, company building",
    'systems-data': "databases, data engineering, networking, low-level systems, security",
    'frontend': "frontend frameworks, UI, UX, visual design",
    'other': "none of the above fits",
}
# 항목마다 이 표시를 남겨 같은 글이 두 번 들어가지 않게 한다.
MARKER = "<!-- gn:{topic_id} -->"


def kst_now():
    return datetime.datetime.now(pytz.timezone('Asia/Seoul'))


def get_target_date_kst():
    # KST 기준 LOOKBACK_DAYS 전 날짜 구하기
    target = kst_now() - datetime.timedelta(days=LOOKBACK_DAYS)
    return target.replace(hour=0, minute=0, second=0, microsecond=0)


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def clean_title(title):
    """제목을 Markdown 링크 텍스트로 안전하게 만든다.

    세 가지를 고친다. RSS 제목에는 `&quot;`·`&#039;` 같은 엔티티가 그대로 실려
    오고, `[유튜브]`처럼 대괄호를 담은 제목은 `[제목](url)` 안에서 링크를
    깨뜨린다. 특히 제목이 대괄호로 시작하면 `[[`가 되어 Obsidian이 위키링크로
    읽는다. 이미 이스케이프된 것을 다시 하지 않도록 앞의 백슬래시를 확인한다.

    마지막으로 `<`를 엔티티로 되돌린다. ROS Discourse의 `What should go in the
    <license> tag?`처럼 태그를 제목에 담는 글이 있는데, 그대로 두면 렌더러가
    HTML 시작 태그로 읽어 닫는 짝을 찾다가 뒤 내용을 삼킨다. `defuse_html()`은
    본문용이라 링크 텍스트 안에서는 백틱이 중첩되므로 여기서는 엔티티를 쓴다 -
    `&lt;license>`는 화면에 `<license>`로 그대로 보인다.
    """
    text = re.sub(r"(?<!\\)([\[\]])", r"\\\1", html.unescape(title))
    return text.replace("<", "&lt;").strip()


def to_markdown(fragment):
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.body_width = 0  # 줄바꿈 방지
    return converter.handle(fragment).strip()


def pending_path(date_str):
    return os.path.join(PENDING_DIR, f"{date_str}.json")


def note_path(date_obj):
    month_folder = f"{date_obj.year}.{date_obj.month}"
    return os.path.join(
        VAULT_DIR, month_folder, f"{date_obj.strftime('%Y-%m-%d')}.md"
    )


def note_exists(date_obj):
    return os.path.exists(note_path(date_obj))


def stash_feed():
    """RSS에 보이는 글을 날짜별 대기 목록에 누적한다.

    점수는 여기서 매기지 않는다. 아직 익지 않았기 때문이다. 같은 글을 여러 번
    보게 되므로 topic id로 중복을 제거한다.
    """
    os.makedirs(PENDING_DIR, exist_ok=True)
    feed = feedparser.parse(GEEKNEWS_RSS)
    if not feed.entries:
        print("⚠️  RSS returned no entries.")
        return

    kst = pytz.timezone('Asia/Seoul')
    by_date = {}
    for entry in feed.entries:
        # published_parsed는 UTC struct_time
        published = datetime.datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
        published_kst = published.astimezone(kst)
        match = TOPIC_ID.search(entry.link)
        if not match:
            continue
        by_date.setdefault(published_kst.strftime('%Y-%m-%d'), []).append({
            'topic_id': match.group(1),
            'title': clean_title(entry.title),
            'link': entry.link,
            'desc': to_markdown(entry.description),
            'date': published_kst.strftime('%H:%M'),
        })

    for date_str, posts in sorted(by_date.items()):
        path = pending_path(date_str)
        existing = []
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception as e:
                print(f"  Could not read {path}: {str(e)[:60]} - starting fresh")
        seen = {post['topic_id'] for post in existing}
        added = [post for post in posts if post['topic_id'] not in seen]
        if not added and existing:
            print(f"  {date_str}: {len(existing)} already stashed, nothing new")
            continue
        merged = existing + added
        merged.sort(key=lambda post: post['date'])
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=1)
        print(f"  {date_str}: stashed {len(merged)} post(s) (+{len(added)})")


def load_pending(date_str):
    path = pending_path(date_str)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_pending(date_str, posts):
    """대기 목록을 덮어쓴다. 조회해 둔 점수와 본문을 함께 남기므로, 요약이
    도중에 막혀 이 날짜를 다시 처리하게 되어도 점수를 또 묻지 않는다."""
    os.makedirs(PENDING_DIR, exist_ok=True)
    with open(pending_path(date_str), 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=1)


def prune_pending():
    """오래된 대기 목록을 지운다. 처리된 날짜는 다시 필요하지 않다."""
    cutoff = (kst_now() - datetime.timedelta(days=PENDING_KEEP_DAYS)).strftime('%Y-%m-%d')
    for path in glob.glob(os.path.join(PENDING_DIR, "*.json")):
        name = os.path.splitext(os.path.basename(path))[0]
        if name < cutoff:
            os.remove(path)
            print(f"  Pruned stale pending list {name}")


def fetch_points_and_body(topic_id):
    """topic 페이지를 한 번 읽어 점수와 본문을 함께 돌려준다.

    점수는 `<span id='tp{id}'>N</span>P`에 있다. 읽을 수 없으면 None을 준다.
    호출한 쪽은 None을 탈락으로 다루지 않는다 — 사이트 구조가 바뀌면 필터가
    조용히 전부 버리게 되기 때문이다.
    """
    try:
        page = fetch(TOPIC_URL.format(topic_id=topic_id))
    except Exception as e:
        print(f"  Lookup failed for {topic_id}: {str(e)[:70]}")
        return None, ""
    found = re.search(rf"id='tp{topic_id}'>(\d+)</span>P", page)
    if not found:
        print(f"  Point markup not found for {topic_id}")
    section = CONTENTS.search(page)
    body = to_markdown(section.group(1)) if section else ""
    return (
        int(found.group(1)) if found else None,
        BODY_HEADING.sub("##### ", body),
    )


def matched_interest(post):
    """제목이 관심어에 걸리면 그 말을 돌려준다. 걸리지 않으면 빈 문자열.

    본문은 보지 않는다. 실측에서 본문까지 검사하면 매칭이 14%에서 23%로
    늘었는데, 늘어난 쪽은 "주식 기사 본문에 Anthropic이 스쳐 지나간" 부류가
    대부분이었다. 반대로 실제로 찾던 글 - `Codex CLI의 세션 로그가 수백 GB`,
    `Claude Code는 프롬프트를 읽기 전 3.3만 토큰을 전송함` - 은 모두 제목에
    관심어가 있었다. 다루는 주제라면 제목에 나온다.
    """
    title = post.get('title', '').lower()
    for term in INTEREST_TERMS:
        if term in title:
            return term
    return ""


def parse_model_json(text):
    """모델이 코드펜스로 감싸 보내는 경우까지 포함해 JSON을 읽는다."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", cleaned)
    return json.loads(cleaned)


def gemini_generate(prompt):
    """Gemini를 한 번 부르고 응답 텍스트를 돌려준다. 실패하면 None.

    호출 자체의 실패 처리는 어느 소스에서 부르든 같으므로 여기 모아 둔다.
    부르는 쪽은 응답을 어떻게 읽을지만 정하면 된다.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Config Error: {e}")
        return None

    for attempt in (1, 2):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt
            )
        except Exception as e:
            # 일일 한도를 넘긴 것이라면 기다려도 그날은 회복되지 않는다. 60초씩
            # 세 번 자고 나서야 포기하면 3분을 헛되이 쓴다.
            if "PerDay" in str(e) or "GenerateRequestsPerDay" in str(e):
                print("Daily free-tier quota is exhausted - not retrying today.")
                return None
            if "429" in str(e) and attempt == 1:
                print("Rate limit exceeded (429). Waiting 60 seconds...")
                time.sleep(60)
                continue
            print(f"Gemini Error: {str(e)[:100]}...") # Truncate error message
            return None
        return response.text

    print("Skipping summary due to rate limit.")
    return None


def summarize_and_classify(title, description):
    """요약과 주제 분류를 한 번의 호출로 받는다.

    분류를 따로 부르면 호출이 두 배가 되지만, 모델은 이미 글을 읽고 있으므로
    같은 응답에서 카테고리까지 받으면 호출 수는 그대로다.

    (요약, 카테고리 키)를 돌려준다. 실패하면 (None, 'other').
    """
    options = "\n".join(f"        - {key}: {hint}"
                        for key, hint in CATEGORY_HINTS.items())
    prompt = f"""
        Summarize the following tech news article in Korean, and classify it.

        Return ONLY a JSON object, no code fence, with exactly these keys:
          "summary": a Korean bulleted list of about 3 lines, each starting with "- "
          "category": exactly one of the keys below

{options}

        Pick "other" rather than forcing a poor fit.

        Title: {title}
        Description: {description}
    """

    text = gemini_generate(prompt)
    if text is None:
        return None, 'other'

    try:
        payload = parse_model_json(text)
    except Exception:
        # 요약은 살리고 분류만 포기한다.
        print(f"  Could not read JSON for '{title[:40]}' - filing under other")
        return text.strip() or None, 'other'

    category = payload.get('category')
    if category not in CATEGORIES:
        print(f"  Unknown category {category!r} for '{title[:40]}' - filing under other")
        category = 'other'
    return (payload.get('summary') or None), category


def scrape_geeknews():
    print("Stashing what RSS currently shows...")
    stash_feed()
    prune_pending()

    target = get_target_date_kst()
    date_str = target.strftime('%Y-%m-%d')

    # 하루에 여러 번 돌려 목록 창을 놓치지 않게 하되, 이미 완성된 날을 다시
    # 채점하지는 않는다. 점수 조회는 글마다 한 번의 요청이므로 낭비가 크다.
    if note_exists(target) and os.getenv("GEEKNEWS_OVERWRITE") != "1":
        print(f"\n{date_str} is already written - skipping scoring.")
        return [], target

    print(f"\nScoring posts from {date_str} (>= {MIN_POINTS}P kept)...")

    candidates = load_pending(date_str)
    if candidates is None:
        print(f"No stashed list for {date_str}. Lists are built one day at a time,")
        print(f"so this becomes available {LOOKBACK_DAYS} day(s) after the first run.")
        return [], target
    print(f"{len(candidates)} post(s) stashed for that day")

    # 점수와 본문을 한 번의 요청으로 함께 읽는다. 앞선 실행이 요약 단계에서
    # 멈췄다면 점수는 이미 대기 목록에 있으니 다시 묻지 않는다.
    scored = []
    fresh = 0
    for post in candidates:
        # `scored` 하나만 본다. 본문이 비는 글(링크만 올라온 항목)도 조회는 끝난
        # 것이므로, 본문 유무를 조건에 넣으면 그런 글만 매번 다시 묻게 된다.
        if post.get('scored'):
            post.setdefault('points', None)
            post.setdefault('body', post.get('desc', ""))
        else:
            points, body = fetch_points_and_body(post['topic_id'])
            post['points'] = points
            post['body'] = body or post.get('desc', "")
            post['scored'] = True
            fresh += 1
            time.sleep(REQUEST_INTERVAL)
        scored.append(post)
    if fresh < len(candidates):
        print(f"  {len(candidates) - fresh}건은 앞선 실행의 점수를 재사용")
    # 다음 실행이 점수를 다시 묻지 않도록 지금 저장한다.
    save_pending(date_str, scored)

    unreadable = [post for post in scored if post['points'] is None]
    if scored and len(unreadable) == len(scored):
        # 점수를 하나도 못 읽었다면 필터가 조용히 전부 버리게 된다. 그보다는
        # 전부 남기고 사람이 알아차리게 한다.
        print("⚠️  No points could be read at all - keeping everything.")
        kept = scored
    else:
        # 점수를 못 읽은 개별 글도 버리지 않는다.
        kept = [post for post in scored
                if post['points'] is None
                or post['points'] >= MIN_POINTS
                or matched_interest(post)]

    by_interest = sum(1 for post in kept
                      if post['points'] is not None
                      and post['points'] < MIN_POINTS)
    print(f"Kept {len(kept)} ({by_interest} by interest term), "
          f"dropped {len(scored) - len(kept)} below {MIN_POINTS}P")

    # 점수 높은 순. 점수를 모르는 글은 뒤에 둔다.
    kept.sort(key=lambda post: (post['points'] is None, -(post['points'] or 0)))

    # 통과한 글만 요약한다. 필터 덕분에 API 호출이 하루 수 건으로 줄어든다.
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 3
    unresolved = 0
    for post in kept:
        post['summary'] = None
        post['category'] = None
        if not GEMINI_API_KEY:
            continue
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            unresolved += 1
            continue

        print(f"Summarizing: {post['title']}...")
        post['summary'], post['category'] = summarize_and_classify(
            post['title'], post['body'][:SUMMARY_INPUT_LIMIT]
        )

        if post['summary'] is None:
            post['category'] = None
            unresolved += 1
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print("🚫 Too many errors. Stopping Gemini summarization for this run.")
        else:
            consecutive_failures = 0 # 성공 시 초기화
            time.sleep(SUMMARY_INTERVAL) # 성공 시 대기 (Rate Limit 방지)

    # 분류가 남았으면 이 날짜를 완성으로 치지 않는다. 429는 중간부터 전멸하는
    # 성격이라, 실패분을 'other'로 적어 두면 주제 문서가 조용히 오염된다.
    # 파일을 쓰지 않고 대기 목록에 점수를 남겨 두면 다음 실행이 이어받는다.
    if unresolved:
        print(f"⚠️  {unresolved}/{len(kept)} unclassified - leaving {date_str} for the next run.")
        print("    Scores are cached, so the retry only spends summary calls.")
        return [], target

    return kept, target


def save_to_markdown(posts, date_obj):
    if not posts:
        print(f"Nothing to save for {date_obj.strftime('%Y-%m-%d')}")
        return

    filename = note_path(date_obj)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    date_str = date_obj.strftime('%Y-%m-%d')
    today_str = kst_now().strftime('%Y-%m-%d')

    # 정상 운영에서는 매일 새 날짜라 충돌하지 않는다. 충돌한다면 이미 수집된 날을
    # 다시 긁고 있다는 뜻이고, 그 파일은 지금보다 낮은 기준으로 모은 글을 더 많이
    # 담고 있을 수 있다. 덮어쓰기는 사람이 결정한다.
    if os.path.exists(filename) and os.getenv("GEEKNEWS_OVERWRITE") != "1":
        print(f"⚠️  {filename} already exists - not overwriting.")
        print("    Re-run with GEEKNEWS_OVERWRITE=1 to replace it.")
        return

    with open(filename, 'w', encoding='utf-8') as f:
        # Frontmatter. type/status/created/updated는 vault의 노트 계약 필수 항목이라
        # 빠지면 vault-gardening이 계약 위반으로 보고한다.
        f.write("---\n")
        f.write("type: article\n")
        f.write("status: seed\n")
        f.write(f"created: {date_str}\n")
        f.write(f"updated: {today_str}\n")
        f.write("tags:\n  - geeknews\n  - daily-scrap\n")
        # 허브와 이어 둔다. 없으면 날짜 파일이 그래프에서 월별 인덱스로만
        # 매달려 있어, 주제 문서 쪽에서 원본으로 돌아올 길이 끊긴다.
        f.write('related:\n  - "[[GeekNews 큐레이션 허브]]"\n')
        f.write("sources: []\n")
        f.write("---\n\n")

        f.write(f"# 📰 GeekNews {date_str}\n\n")
        f.write(f"> Scraped at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        f.write(f" · {MIN_POINTS}P 이상만 수집 · 게시 후 약 {LOOKBACK_DAYS}일 시점 점수\n\n")

        for post in posts:
            f.write(f"## [{post['title']}]({post['link']})\n")
            points = post.get('points')
            line = f"{points}P" if points is not None else "점수 미확인"
            # 점수 미달인데 남았다면 관심어 때문이다. 왜 들어왔는지 적어 둔다.
            if points is not None and points < MIN_POINTS:
                term = matched_interest(post)
                if term:
                    line += f" (관심어: {term})"
            f.write(f"- **Points**: {line}\n")
            f.write(f"- **Date**: {post['date']}\n")
            # 분류 결과를 원본에도 남긴다. 기준이 바뀌어 주제 문서를 다시 만들 때
            # 무엇이 어디로 갔는지 되짚을 수 있다.
            category = post.get('category') or 'other'
            f.write(f"- **Topic**: {CATEGORIES.get(category, CATEGORIES['other'])}\n\n")

            if post.get('summary'):
                f.write(f"{post['summary']}\n\n")
            else:
                f.write(f"{post['body']}\n\n")

            f.write("---\n")

    print(f"Saved {len(posts)} posts to {filename}")


def refresh_month_index(date_obj):
    """그 달의 아카이브 인덱스를 폴더 목록에서 다시 만든다.

    스크래퍼가 날짜 파일만 쓰고 인덱스를 손대지 않아, 새로 수집한 날이 그래프에서
    고립됐다 - 실측에서 `2026-07-25`가 인바운드 0으로 고아 노트로 잡혔다. 다른
    달은 일괄 정리 때 인덱스가 함께 만들어져 온전했으므로, 매일 새로 생기는
    파일만 빠지는 구조였다.

    한 줄을 덧붙이는 대신 목록 전체를 폴더에서 다시 만든다. 인덱스는 파일에서
    재생산되는 파생물이므로 그래야 과거에 빠진 것도 함께 메워지고, 손으로 지운
    줄이 조용히 남지도 않는다. 내용이 같으면 쓰지 않아 실행마다 mtime을
    건드리지 않는다.
    """
    month = f"{date_obj.year}.{date_obj.month}"
    folder = os.path.join(VAULT_DIR, month)
    if not os.path.isdir(folder):
        return

    dates = sorted(
        os.path.splitext(name)[0]
        for name in os.listdir(folder)
        if name.endswith(".md")
    )
    if not dates:
        return

    path = os.path.join(VAULT_DIR, f"{month} 인덱스.md")
    today_str = kst_now().strftime('%Y-%m-%d')

    # `created`는 처음 만든 날이므로 보존한다.
    created = today_str
    previous = ""
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            previous = f.read()
        found = re.search(r"^created: (\S+)", previous, re.M)
        if found:
            created = found.group(1)

    listing = "\n".join(f"- [[{date}]]" for date in dates)
    text = (
        "---\n"
        "type: index\n"
        "status: evergreen\n"
        f"created: {created}\n"
        f"updated: {today_str}\n"
        "tags:\n  - GeekNews\n  - Archive\n"
        'related:\n  - "[[GeekNews 큐레이션 허브]]"\n'
        "sources: []\n"
        "---\n\n"
        f"# 📰 GeekNews {month} 아카이브 인덱스\n\n"
        "> [!NOTE]\n"
        f"> {month} 월에 자동 수집된 GeekNews 일일 리포트 {len(dates)}개의"
        " 전체 목차 및 링크 인덱스입니다.\n\n"
        "## 일일 뉴스 리포트 목록\n\n"
        f"{listing}\n"
    )

    # `updated` 한 줄만 다른 경우까지 새로 쓰면 인덱스가 매 실행 갱신된다.
    if previous:
        strip = lambda s: re.sub(r"^updated: .*$", "", s, count=1, flags=re.M)
        if strip(previous) == strip(text):
            return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  {month} 인덱스 {len(dates)}건 갱신")


def topic_note_header(name, today_str):
    """주제 문서를 처음 만들 때의 머리말.

    `related`는 비워 둔다. 어떤 원자적 노트와 이어지는지는 사람이 한 번 정하는
    편이 낫다 — 자동으로 매번 판단하게 하면 오연결이 쌓이고, 고정해 두면 분류가
    틀린 날에도 그래프는 망가지지 않는다.
    """
    return (
        "---\n"
        "type: moc\n"
        "status: developing\n"
        f"created: {today_str}\n"
        f"updated: {today_str}\n"
        "tags:\n  - geeknews\n  - curation\n"
        "related: []\n"
        "sources: []\n"
        "---\n\n"
        f"# {name}\n\n"
        "> [!NOTE]\n"
        f"> GeekNews 자동 수집분 중 {MIN_POINTS}P 이상인 글을 주제별로 모은 큐레이션\n"
        "> 대기열입니다. 각 항목의 한 줄 요약은 **검증되지 않은 AI 생성 요약**이며\n"
        "> 근거가 아닙니다. 원문을 읽고 판단할 대상의 목록으로만 쓰세요.\n"
        "> 날짜순 원본은 `GeekNews/<연월>/`에 그대로 있습니다.\n\n"
        "> [!TIP]\n"
        "> 이 문서와 이어지는 원자적 노트는 frontmatter의 `related`에 직접\n"
        "> 적어 주세요. 자동 수집은 그 값을 건드리지 않습니다.\n"
    )


def defuse_html(text):
    """날것의 태그를 인라인 코드로 감싼다.

    `<script>` 태그 한 줄만 추가하면...` 같은 요약이 그대로 들어가면, 렌더러는
    그것을 HTML 블록의 시작으로 읽고 닫는 태그를 찾다가 문서 끝까지 삼킨다.
    실제로 주제 문서 하나가 그 지점부터 아래 전체가 렌더링되지 않았다.
    """
    return re.sub(r"(?<!`)(<!?/?[a-zA-Z][a-zA-Z0-9]*[^>\n]*>)(?!`)", r"`\1`", text)


def first_line(summary):
    """요약의 첫 항목만 한 줄로 뽑는다. 주제 문서는 목록이기 때문이다."""
    if not summary:
        return ""
    for line in summary.splitlines():
        stripped = line.strip().lstrip("-*• ").strip()
        if stripped:
            return defuse_html(re.sub(r"\s+", " ", stripped))
    return ""


def file_into_topics(posts, date_obj):
    """분류된 글을 주제 문서에 덧붙인다.

    같은 글을 두 번 넣지 않기 위해 항목 끝의 `<!-- gn:id -->` 표시를 확인한다.
    """
    if not posts:
        return

    os.makedirs(TOPIC_DIR, exist_ok=True)
    today_str = kst_now().strftime('%Y-%m-%d')
    month_heading = f"## {date_obj.strftime('%Y-%m')}"

    grouped = {}
    for post in posts:
        grouped.setdefault(post.get('category') or 'other', []).append(post)

    for category, items in grouped.items():
        name = CATEGORIES.get(category, CATEGORIES['other'])
        path = os.path.join(TOPIC_DIR, f"{name}.md")

        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                text = f.read()
        else:
            text = topic_note_header(name, today_str)

        # 같은 날 안에서는 점수 높은 순으로 넣는다.
        items = sorted(items, key=lambda p: -(p.get('points') or 0))
        day = date_obj.strftime('%m-%d')
        lines = []
        for post in items:
            marker = MARKER.format(topic_id=post['topic_id'])
            if marker in text:
                continue
            points = post.get('points')
            score = f"**{points}P**" if points is not None else "**점수 미확인**"
            # 점수 미달인데 남았다면 관심어 때문이다. 왜 남았는지 적어 둔다.
            if points is not None and points < MIN_POINTS:
                term = matched_interest(post)
                if term:
                    score = f"**{points}P (관심어: {term})**"
            note = first_line(post.get('summary'))
            entry = f"- {score} `{day}` [{post['title']}]({post['link']})"
            if note:
                entry += f" — {note}"
            lines.append(f"{entry} {marker}")

        if not lines:
            print(f"  {name}: already filed")
            continue

        # 최신이 위로 온다. 수집은 날마다 이어지므로 새 항목은 언제나 문서에
        # 이미 있는 무엇보다 최근이고, 맨 아래에 붙이면 읽는 사람이 매번 끝까지
        # 스크롤해야 한다.
        block = "\n".join(lines)
        if month_heading in text:
            # 이 달 묶음의 첫 항목 앞에 끼운다.
            insert = text.index(month_heading) + len(month_heading)
            rest = text[insert:].lstrip("\n")
            text = text[:insert] + "\n\n" + block + "\n" + rest
        else:
            # 새 달은 기존 월 섹션 전체보다 앞에 둔다. 월 섹션이 아직 없으면
            # 머리말 뒤에 붙인다.
            first_month = text.find("\n## ")
            if first_month == -1:
                text = text.rstrip("\n") + f"\n\n{month_heading}\n\n" + block + "\n"
            else:
                text = (text[:first_month].rstrip("\n")
                        + f"\n\n{month_heading}\n\n" + block + "\n"
                        + text[first_month:])

        text = re.sub(r"^updated: .*$", f"updated: {today_str}", text,
                      count=1, flags=re.M)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  {name}: +{len(lines)}")


def feed_note_header(source, today_str):
    """소스별 목록 문서의 머리말. 노트 계약의 필수 항목을 채운다."""
    tags = "".join(f"  - {tag}\n" for tag in source['tags'])
    return (
        "---\n"
        "type: moc\n"
        "status: developing\n"
        f"created: {today_str}\n"
        f"updated: {today_str}\n"
        f"tags:\n{tags}"
        f'related:\n  - "[[{source["hub"]}]]"\n'
        "sources: []\n"
        "---\n\n"
        f"# {source['name']}\n\n"
        "> [!NOTE]\n"
        "> 발행된 제목과 링크만 자동으로 쌓는 대기열입니다. 요약하지 않으므로\n"
        "> 여기 있는 어떤 줄도 내용에 대한 주장이 아닙니다. 읽을 것을 고르는\n"
        "> 목록으로만 쓰고, 읽은 뒤의 이해는 원자적 노트에 적으세요.\n"
    )


def scrape_feed_source(key, source):
    """일반 RSS 소스의 새 글을 제목과 링크만으로 쌓는다.

    GeekNews와 달리 대기 목록도, 요약도 쓰지 않는다. 채점할 점수가 없으니 미룰
    이유가 없고, 본문을 읽지 않으니 API 호출도 없다. 중복은 줄 끝의 마커로
    막으므로 하루에 몇 번을 돌려도 같은 글이 두 번 들어가지 않는다.
    """
    print(f"\n=== {source['name']} ===")
    feed = feedparser.parse(source['rss'])
    if not feed.entries:
        print(f"⚠️  {source['name']}: RSS returned no entries.")
        return

    kst = pytz.timezone('Asia/Seoul')
    cutoff = kst_now() - datetime.timedelta(days=source['window_days'])
    today_str = kst_now().strftime('%Y-%m-%d')
    path = os.path.join(WIKI_ROOT, source['path'])

    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            text = f.read()
    else:
        text = feed_note_header(source, today_str)

    # 로봇 전용이 아닌 피드에서 관련 글만 받을 때 쓴다. 제목만 검사하는 이유는
    # GeekNews의 관심어와 같다 - 본문까지 보면 주제가 스쳐 지나간 글이 대거
    # 걸리고, 정작 찾던 글은 제목에 그 말이 있다.
    title_filter = source.get('title_filter')

    fresh = []
    undated = 0
    filtered = 0
    for entry in feed.entries:
        if not getattr(entry, "published_parsed", None):
            undated += 1
            continue
        published = datetime.datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
        published_kst = published.astimezone(kst)
        if published_kst < cutoff:
            continue
        if title_filter:
            lowered = (entry.title or "").lower()
            if not any(term in lowered for term in title_filter):
                filtered += 1
                continue
        marker = FEED_MARKER.format(key=key, uid=entry.link)
        if marker in text:
            continue
        fresh.append({
            'dt': published_kst,
            'title': clean_title(entry.title),
            'link': entry.link,
            'marker': marker,
        })
    if undated:
        print(f"  {undated}건은 발행일이 없어 건너뜀")
    if filtered:
        print(f"  {filtered}건은 제목 필터에 걸리지 않아 제외")
    if not fresh:
        print(f"  새 글 없음 (최근 {source['window_days']}일)")
        return

    # 같은 달 안에서는 최신이 위로 온다.
    fresh.sort(key=lambda post: post['dt'], reverse=True)
    by_month = {}
    for post in fresh:
        by_month.setdefault(post['dt'].strftime('%Y-%m'), []).append(post)

    # 오래된 달부터 끼운다. 새 달은 언제나 기존 내용 앞에 들어가므로, 이 순서로
    # 넣어야 마지막에 최신 달이 맨 위에 온다.
    for month in sorted(by_month):
        heading = f"## {month}"
        block = "\n".join(
            f"- `{post['dt'].strftime('%m-%d')}` "
            f"[{post['title']}]({post['link']}) {post['marker']}"
            for post in by_month[month]
        )
        if heading in text:
            insert = text.index(heading) + len(heading)
            rest = text[insert:].lstrip("\n")
            text = text[:insert] + "\n\n" + block + "\n" + rest
        else:
            first_month = text.find("\n## ")
            if first_month == -1:
                text = text.rstrip("\n") + f"\n\n{heading}\n\n" + block + "\n"
            else:
                text = (text[:first_month].rstrip("\n")
                        + f"\n\n{heading}\n\n" + block + "\n"
                        + text[first_month:])

    text = re.sub(r"^updated: .*$", f"updated: {today_str}", text,
                  count=1, flags=re.M)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  +{len(fresh)}건")


def run_geeknews():
    """GeekNews 파이프라인 한 번. 채점 → 요약·분류 → 원본 → 주제 문서."""
    posts, date_obj = scrape_geeknews()
    save_to_markdown(posts, date_obj)
    if posts:
        print("Filing into topic notes...")
        file_into_topics(posts, date_obj)
    # 파일을 새로 쓰지 않은 실행에서도 부른다. 인덱스가 폴더와 어긋나 있을 수
    # 있고, 같으면 아무것도 쓰지 않으므로 비용이 없다.
    refresh_month_index(date_obj)


if __name__ == "__main__":
    unknown = [key for key in ENABLED if key not in SOURCES]
    if unknown:
        # 오타를 조용히 넘기면 켰다고 믿은 소스가 영영 수집되지 않는다.
        print(f"⚠️  카탈로그에 없는 소스: {', '.join(unknown)}")
    if not [key for key in ENABLED if key in SOURCES]:
        print("켜진 소스가 없습니다. sources.local.toml의 enabled를 확인하세요.")

    # 한 소스의 실패가 다음 소스를 막아서는 안 된다.
    for key in ENABLED:
        source = SOURCES.get(key)
        if not source:
            continue
        if source.get('needs_api_key') and not GEMINI_API_KEY:
            print(f"⚠️  {source['name']}: GEMINI_API_KEY가 없어 건너뜁니다.")
            continue
        try:
            if source['pipeline'] == 'geeknews':
                run_geeknews()
            else:
                scrape_feed_source(key, source)
        except Exception as e:
            print(f"⚠️  {source['name']} failed: {str(e)[:120]}")
