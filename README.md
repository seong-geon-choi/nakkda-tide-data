# nakkda-tide-data

낚시 앱 **낚.다(nakkda)** 용 조석예보(고저조) 캐시 데이터.

국립해양조사원(KHOA) 조석예보를 [data.go.kr](https://www.data.go.kr/) `tideFcstHghLw` API에서
하루 한 번 받아 관측소별 JSON으로 저장한다. 앱은 KHOA를 직접 호출하는 대신 이 저장소의
CDN(jsDelivr / GitHub Pages)에서 데이터를 받아 기기에 캐시한다.
→ 사용자 수가 늘어도 KHOA 호출량은 **하루 ~1,000건으로 고정**(개발키 한도 10,000/일의 10%).

## 구조

```
scripts/fetch_tides.py   수집 스크립트 (환경변수 KHOA_SERVICE_KEY 필요)
scripts/stations.json    관측소 62개소 (code, name, lat, lng) — 앱과 동기
data/DT_0001.json …      관측소별 조석예보 (오늘 전후 윈도우)
data/manifest.json       생성시각·윈도우·관측소 목록
.github/workflows/update-tides.yml   매일 KST 05:00 자동 갱신
```

## 데이터 포맷 (`data/<obsCode>.json`)

```json
{
  "station": "DT_0001",
  "name": "인천",
  "generated": "2026-10-21T21:00:00+00:00",
  "days": {
    "20261021": [
      { "t": "H", "time": "03:12", "level": 704 },
      { "t": "L", "time": "09:40", "level": 120 }
    ]
  }
}
```
- `t`: `"H"` 고조(만조) / `"L"` 저조(간조)
- `time`: `HH:mm` (KST)
- `level`: 조위(cm), 없으면 `null`

## CDN URL

- jsDelivr: `https://cdn.jsdelivr.net/gh/seong-geon-choi/nakkda-tide-data@main/data/DT_0001.json`
- GitHub Pages(활성화 시): `https://seong-geon-choi.github.io/nakkda-tide-data/data/DT_0001.json`

## 운영

- 수동 갱신: Actions 탭 → **update-tides** → *Run workflow*.
- 서비스키 교체: 저장소 *Settings → Secrets and variables → Actions* 의 `KHOA_SERVICE_KEY`.
