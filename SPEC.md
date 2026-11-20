# 명세: URL 단축기

## 1. 무엇을 만드는가

사용자가 절대 HTTP(S) URL을 입력하면 재현 가능한 짧은 코드를 만들고, 그 코드로
원래 URL을 조회하는 교육용 URL 단축기다. 직접 구현한 해시 테이블의 충돌 처리와
탐색 비용을 웹 화면과 실험으로 살펴본다.

## 2. base62 인코딩

- `src/base62.py`의 `encode(value: int) -> str`와 `decode(encoded: str) -> int`를 쓴다.
- 알파벳 순서는 `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`다.
- 0은 `"0"`으로 인코딩한다. 음수는 `ValueError`, 정수가 아닌 입력은 `TypeError`다.
- 빈 문자열 또는 알파벳 밖 문자가 있는 입력은 `ValueError`다.

## 3. 해시 테이블

- 문자열 키와 임의의 값을 저장하는 `HashTable(capacity=8)`을 만든다. 용량 길이의
  리스트를 버킷 배열로 쓰고, 각 버킷은 `(key, value)` 쌍을 담은 리스트다.
- 충돌 처리는 개별 체이닝(separate chaining)이다. 각 문자열 키는 왼쪽부터 한
  문자씩 Horner 식 `h = (31 * h + ord(character)) % capacity`에 넣어 버킷
  인덱스를 구한다. 초기값은 `h = 0`이며 빈 문자열의 인덱스는 0이다.
- `set(key, value)`는 새 키를 추가하고, 같은 키가 있으면 값을 바꾼다.
- `get(key, default=None)`은 값을 돌려준다. 키가 없고 기본값을 주지 않았으면
  `KeyError`를 낸다. `delete(key)`는 삭제 성공 여부를 bool로 돌려준다.
- `search(key)`는 `(found, value, probes)`를 돌려준다. `probes`는 실제 비교한
  항목 수이며 비어 있는 체인을 찾을 때는 0이다. `slots()`와 `hash_steps(key)`는
  화면·실험에 사용할 진단 정보를 돌려준다.
- 용량은 양의 정수이며 자동으로 늘리지 않는다. `src/`에서는 내장 `dict`, `set`,
  `hash()`를 사용하지 않는다. 저장·조회·충돌 처리는 직접 구현한 리스트 기반
  해시 테이블과 명시한 Horner 계산으로 수행한다.
- `LinearProbingHashTable`도 같은 인터페이스를 제공한다. 선형 탐지는 삭제 표식을
  두어 탐색 체인을 보존하고, 가득 찬 테이블에 새 키를 넣으면 `OverflowError`를
  낸다. 선형 탐지의 비교 수는 성공한 슬롯과 탐색을 끝내는 빈 슬롯을 포함해
  방문한 슬롯 수로 센다.

## 4. 단축기

- `Shortener(table_type="chaining", capacity=1024)`는 `chaining` 또는 `linear`
  테이블 두 개를 사용해 URL→코드와 코드→URL을 저장한다.
- `shorten(url)`은 첫 입력 시 순차 정수 ID의 base62 코드를 만들고, 같은 URL이면
  같은 코드를 돌려준다. 코드는 `"1"`부터 시작한다.
- URL은 공백이 없고 scheme이 `http` 또는 `https`이며 호스트가 있는 절대 URL이어야
  한다. 그렇지 않으면 `ValueError`를 낸다.
- `expand(code)`는 원래 URL을 돌려준다. 알 수 없는 코드는 `KeyError`다.
- 해시 테이블은 고정 용량이므로 저장 공간이 부족하면 그 테이블의 오류를 그대로
  전달한다.

## 5. 웹 서버

- `python3 -m src.server --port 8000` 또는 `make serve`로 표준 라이브러리 HTTP
  서버를 실행한다.
- `GET /`은 URL 입력 폼을, `POST /shorten`은 코드와 단축 링크를 보여 준다.
- `GET /<code>`는 코드를 확장해 HTTP 302로 원래 URL에 이동시킨다. 없는 코드는
  404로 응답한다.
- `GET /table`은 버킷/슬롯, 방문한 칸 수, Horner 해시 계산 과정을 보여 준다.
  `?table=chaining` 또는 `?table=linear`로 탐색 방식을 선택한다.
- 포트 공개·휴대폰 확인은 Codespaces의 포트 UI에서 직접 수행한다. 서버 종료 후
  포트 공개 설정을 비공개로 되돌린다.

## 6. 경계 사례와 검증

- base62: 0, 61/62 경계, 큰 정수 왕복, 음수, 잘못된 타입, 빈 문자열, 잘못된 문자.
- 해시 테이블: 용량 검증, 충돌, 덮어쓰기, 키 없음, 삭제, 마지막 항목 삭제 후 재삽입.
- 선형 탐지: 끝 슬롯에서 0번 슬롯으로 순환, 삭제 표식 이후 탐색, 중복 키,
  가득 찬 테이블, 빈 슬롯 검색.
- 단축기: 같은 URL 재입력, 서로 다른 URL, 잘못된 scheme/host, 없는 코드, 용량 초과.
- HTTP: 입력 폼, 성공/잘못된 입력, 리다이렉트, 없는 코드, 테이블 진단 화면.
- 실험: 동일한 고정 키 집합과 용량에서 적재율 0.1~0.9의 평균 슬롯/노드 방문
  횟수를 표·SVG로 비교하고 2쪽 이내 PDF 보고서를 만든다. 체이닝은 성공
  `1 + α/2`, 실패 `α`; 선형 탐지는 성공 `1/2 × (1 + 1/(1-α))`, 실패
  `1/2 × (1 + 1/(1-α)^2)` 근사 기대값과 비교한다.
