export const LANGUAGES = ['en', 'ko'];

const korean = {
  'Skip to content': '본문으로 건너뛰기',
  'Go to the documentation gateway': '학습 문서 홈으로',
  'Search docs': '문서 검색',
  'Open GitHub repository': 'GitHub 저장소 열기',
  'Change color theme': '화면 테마 변경',
  'Display language': '표시 언어',
  'Loading learning paths.': '학습 문서를 불러오는 중입니다.',
  'Official sources first. Examples make ideas concrete.': '공식 근거를 확인하고, 예제로 이해합니다.',
  'View source on GitHub': 'GitHub에서 원문 보기',
  'DIAGRAM VIEWER': '다이어그램 보기',
  'Expanded diagram': '확대한 다이어그램',
  'Diagram zoom controls': '다이어그램 확대·축소',
  'Zoom out': '축소',
  'Zoom in': '확대',
  'Fit to screen': '화면에 맞추기',
  'Close': '닫기',
  'Zoom in and scroll to explore the details. You can also zoom with Ctrl or ⌘ and the mouse wheel.': '확대한 뒤 스크롤하여 세부 내용을 살펴보세요. Ctrl 또는 ⌘를 누른 채 마우스 휠로도 확대할 수 있습니다.',
  'Learn operations.': '운영을 배우고,',
  'Go deeper.': '깊이 이해하세요.',
  'Search a topic or keyword': '주제나 키워드 검색',
  'learn': '학습',
  'connect': '연결',
  'operate': '운영',
  'Documentation overview': '학습 문서 현황',
  'learning paths': '학습 경로',
  'topics': '주제',
  'documents': '문서',
  'CHOOSE A PATH': '학습 경로 선택',
  'Choose your learning path': '학습 경로를 선택하세요',
  'Build systems with DevOps, connect models with AIOps, and follow events into trusted data with Data & Observability.': 'DevOps로 시스템을 구축하고, AIOps로 모델과 운영을 연결하며, 데이터·관측성 과정에서 신뢰할 수 있는 데이터의 흐름을 살펴보세요.',
  '{topics} topics · {documents} documents': '주제 {topics}개 · 문서 {documents}개',
  '{count} documents': '문서 {count}개',
  '{count} min': '{count}분',
  'About {count} min': '약 {count}분',
  '{documents} documents · About {minutes} min': '문서 {documents}개 · 약 {minutes}분',
  'Build operational judgment through essential terms, working examples, failures, and recovery.': '핵심 용어와 실행 예제, 장애·복구 경험으로 운영 판단력을 기릅니다.',
  'Problem → Key terms → Baseline → Failure → Recovery → Operational judgment': '문제 → 핵심 용어 → 정상 동작 → 장애 → 복구 → 운영 판단',
  'Start with plain explanations and connect technical terms to observable evidence.': '쉬운 설명에서 시작해 기술 용어를 관찰 가능한 근거와 연결하세요.',
  'All learning paths': '전체 학습 경로',
  'CHOOSE A TOPIC': '주제 선택',
  '{title} learning path': '{title} 학습 경로',
  'Each topic moves from problems and terms to observing a baseline, isolating failures, verifying recovery, and making operational decisions.': '각 주제는 문제와 용어에서 시작해 정상 동작 관찰, 장애 원인 구분, 복구 검증, 운영 판단으로 이어집니다.',
  'Learning stages from foundations to operational judgment': '기초부터 운영 판단까지의 학습 단계',
  '1. Problems and terms': '1. 문제와 용어',
  'Understand the problem and unpack unfamiliar terms.': '해결할 문제를 이해하고 낯선 용어를 익힙니다.',
  '2. Observe the baseline': '2. 정상 동작 관찰',
  'Run a small example and record evidence of normal behavior.': '작은 예제를 실행하고 정상 동작의 근거를 기록합니다.',
  '3. Isolate the failure': '3. 장애 원인 구분',
  'Change one condition and find where the flow stops.': '조건 하나를 바꾸고 흐름이 멈추는 지점을 찾습니다.',
  '4. Verify recovery': '4. 복구 검증',
  'Check that the expected user outcome has been restored.': '사용자가 기대하는 결과가 복구되었는지 확인합니다.',
  '5. Operational judgment': '5. 운영 판단',
  'Explain tradeoffs in security, reliability, performance, and cost.': '보안·신뢰성·성능·비용 사이의 선택을 설명합니다.',
  'READING ORDER': '읽는 순서',
  'Follow this reading order': '이 순서로 학습하세요',
  'Start with the roadmap, then work through the concepts and labs in order.': '로드맵부터 시작해 개념과 실습을 순서대로 진행하세요.',
  '{title} documents': '{title} 문서 목록',
  'Markdown source ↗': 'Markdown 원문 ↗',
  'Previous and next documents': '이전·다음 문서',
  'Previous document': '이전 문서',
  'Next document': '다음 문서',
  'Click to expand': '클릭하여 확대',
  'Expand': '확대',
  'Enlarged diagram': '확대한 다이어그램',
  '“{query}” search — {title}': '“{query}” 검색 — {title}',
  'Gateway': '학습 홈',
  'SEARCH ALL DOCUMENTS': '전체 문서 검색',
  '{count} documents found.': '문서 {count}개를 찾았습니다.',
  'No matching documents.': '일치하는 문서가 없습니다.',
  'Try different wording or a shorter keyword.': '다른 표현이나 더 짧은 키워드로 검색해 보세요.',
  'Could not load the documents.': '문서를 불러오지 못했습니다.',
  'The language switch changes the site interface. Document text and code remain in English.': '언어 버튼은 사이트 메뉴를 전환합니다. 문서 본문과 코드는 영어 원문으로 제공됩니다.',
};

const pathCopy = {
  infra: ['DevOps', 'Linux·네트워크·AWS·Kubernetes부터 백엔드 계약, 데이터, 보안, 트래픽, 신뢰성까지 시스템을 구축하고 운영합니다.'],
  aiops: ['AIOps', 'AI 모델·검색·에이전트를 GPU·MLOps 플랫폼, 근거 기반 진단, 통제된 자동 복구와 연결합니다.'],
  'data-observability': ['데이터·관측성', 'Parquet, 레이크하우스 테이블, Spark, Kafka, 품질, OpenTelemetry, 계보, 거버넌스, 관리형 플랫폼을 따라 데이터와 AI의 흐름을 학습합니다.'],
};

const topicCopy = {
  kubernetes: ['Kubernetes', '컨테이너 하나를 실행하는 것부터 시작해 여러 애플리케이션을 자동 배포·교체·연결하고 안전하게 운영하는 과정을 배웁니다.'],
  linux: ['Linux 시스템 운영', '웹 서버 하나가 실행되고 CPU·메모리·디스크·네트워크를 사용하는 방식에서 Linux 장애 진단을 시작합니다.'],
  networking: ['네트워크와 요청 경로', '브라우저에 입력한 주소가 서버 응답으로 돌아올 때까지 이름 조회·연결·암호화·HTTP 단계를 차례로 확인합니다.'],
  'aws-foundations': ['AWS 인프라 기초', 'AWS 계정·권한·리전·가상 네트워크부터 리소스 소유권과 접근 경계를 익힙니다.'],
  'terraform-aws': ['AWS와 Terraform', '클릭으로 만든 AWS 리소스를 코드로 표현하고, 변경 계획을 검토해 안전하게 반영하는 과정을 배웁니다.'],
  'helm-gitops': ['Helm 차트와 GitOps', '반복되는 Kubernetes YAML을 차트와 값으로 구성하고, Git에 선언한 상태를 실제 배포와 일치시키는 과정을 배웁니다.'],
  'observability-sre': ['관측성과 SRE', '느린 서비스를 지표·이벤트 기록·요청 경로로 나누어 살펴보고, 사용자가 받는 결과를 서비스 목표와 연결합니다.'],
  postgresql: ['PostgreSQL 운영', '여러 요청이 동시에 데이터를 변경할 때 무엇이 보이고 남는지부터 잠금·백업·복구를 배웁니다.'],
  nosql: ['Redis와 DynamoDB', '잠시 보관할 빠른 데이터와 오래 유지할 데이터를 구분하고, 주요 조회 방식에 맞춰 저장 구조를 선택합니다.'],
  'infrastructure-security': ['인프라 보안', '누가 요청했고 무엇을 할 수 있는지부터 비밀 정보와 배포 산출물을 안전하게 관리하는 방법을 배웁니다.'],
  messaging: ['메시징과 이벤트 인프라', '서비스 사이에 메시지를 보관하면 무엇이 달라지는지, 중복·순서 변경·반복 실패를 어떻게 처리하는지 배웁니다.'],
  'reliability-finops': ['신뢰성·재해 복구·FinOps', '서비스 성공 목표와 장애 후 데이터 복구 범위·시간을 비용과 함께 결정합니다.'],
  karpenter: ['Karpenter 심화', '실행할 서버가 없어 대기 중인 Pod를 위한 AWS 서버를 만들고, 필요가 줄면 안전하게 축소하는 방법을 배웁니다.'],
  'traffic-resilience': ['트래픽 제어와 서비스 복원력', '게이트웨이·라우트의 책임을 나누고 타임아웃, 재시도 예산, 서킷 브레이커, 이상 인스턴스 탐지로 장애 확산을 막습니다.'],
  'backend-engineering': ['프로덕션 백엔드 엔지니어링', 'HTTP 요청이 도메인 규칙·트랜잭션·저장소·이벤트·캐시를 거쳐 과부하와 변경 속에서도 검증 가능한 결과로 남는 전체 경로를 배웁니다.'],
  'ai-specialist-core': ['AI 핵심 모델과 응용', 'LLM·비전·생성 모델·온디바이스 AI·시계열·추천·RAG·GraphRAG·MCP를 모델 구조와 평가 기준으로 연결합니다.'],
  'ai-transformation-platform': ['AI Transformation 운영 플랫폼', 'GPU 학습·추론 인프라, MLOps·LLMOps, AI DevOps·FinOps, 권한을 통제하는 에이전트를 데이터·평가·배포 기록으로 연결합니다.'],
  'aiops-foundations': ['AIOps 신호와 운영 토폴로지', 'AI를 도입하기 전에 지표·로그·트레이스·이벤트·변경을 같은 서비스와 시간축으로 연결하고 학습 가능한 사고 기록을 만듭니다.'],
  'aiops-diagnosis': ['이상 탐지와 근거 기반 장애 진단', '정적 규칙·기준선·상관 분석으로 원인 후보를 좁히고, LLM을 포함한 진단 주체가 확인한 근거와 불확실성을 남깁니다.'],
  'aiops-remediation': ['승인된 자동 복구와 운영 학습', '권한·사전 조건·영향 범위·중단 조건·롤백·사후 검증을 갖춘 런북으로 진단 결과를 실행에 연결합니다.'],
  'data-observability-engineering': ['데이터·관측성 엔지니어링', '로컬 결과 검증부터 분산 데이터, 텔레메트리, 거버넌스를 적용한 AI, 복구 검증까지 단계적으로 학습합니다.'],
};

export function localizeCatalog(original, language) {
  if (language !== 'ko') return original;
  const localize = (items, copy) => items.map((item) => copy[item.id]
    ? {...item, title: copy[item.id][0], label: copy[item.id][0], description: copy[item.id][1]}
    : item);
  return {
    ...original,
    site: {...original.site, title: '학습 가이드', eyebrow: '주제별 학습 경로',
      description: '시스템과 신뢰할 수 있는 데이터, 운영 근거, 진단·복구를 통해 DevOps·AIOps·데이터 및 관측성 엔지니어링을 배웁니다.'},
    paths: localize(original.paths, pathCopy),
    topics: localize(original.topics, topicCopy),
  };
}

export function message(key, language = 'en', values = {}) {
  const text = language === 'ko' ? (korean[key] ?? key) : key;
  return text.replace(/\{(\w+)\}/g, (placeholder, name) => String(values[name] ?? placeholder));
}

export function savedLanguage(storage) {
  try {
    const value = storage.getItem('docs-language');
    return LANGUAGES.includes(value) ? value : 'en';
  } catch {
    return 'en';
  }
}

export function rememberLanguage(storage, language) {
  if (!LANGUAGES.includes(language)) return;
  try { storage.setItem('docs-language', language); } catch { /* The toggle also works without storage. */ }
}
