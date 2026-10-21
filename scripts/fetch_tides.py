"""국립해양조사원(KHOA) 조석예보(고저조)를 data.go.kr에서 받아 관측소별 JSON으로 저장.

사용자 수와 무관하게 하루 1회 62개소 × 윈도우(약 17일)만 호출하므로
data.go.kr 개발키 한도(10,000/일)의 약 10%만 사용한다.

환경변수 KHOA_SERVICE_KEY 필요(GitHub Actions Secret).
"""
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

BASE = ("https://apis.data.go.kr/1192136/tideFcstHghLw/"
        "GetTideFcstHghLwApiService")
KEY = os.environ.get("KHOA_SERVICE_KEY", "")
ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIONS = json.loads(
    (ROOT / "scripts" / "stations.json").read_text(encoding="utf-8"))

PAST, FUTURE = 2, 14  # 윈도우: 오늘-2 ~ 오늘+14 (총 17일)


def fetch_day(code, yyyymmdd):
    q = urllib.parse.urlencode({
        "serviceKey": KEY,
        "obsCode": code,
        "date": yyyymmdd,
        "numOfRows": "10",
        "pageNo": "1",
        "type": "json",
    })
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=15) as r:
        body = json.loads(r.read().decode("utf-8"))
    items = (body.get("body") or {}).get("items", {})
    item = items.get("item") if isinstance(items, dict) else None
    if item is None:
        return []
    if isinstance(item, dict):
        item = [item]
    out = []
    for e in item:
        dt = str(e.get("predcDt", ""))  # "YYYY-MM-DD HH:MM"
        if len(dt) < 16:
            continue
        extr = str(e.get("extrSe", ""))
        try:
            level = round(float(e.get("predcTdlvVl", 0)))
        except (TypeError, ValueError):
            level = None
        out.append({
            "t": "H" if extr in ("1", "3") else "L",
            "time": dt[11:16],
            "level": level,
        })
    out.sort(key=lambda x: x["time"])
    return out


def main():
    if not KEY:
        print("ERROR: KHOA_SERVICE_KEY not set", file=sys.stderr)
        return 1

    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=d)).strftime("%Y%m%d")
             for d in range(-PAST, FUTURE + 1)]
    gen = datetime.datetime.now(
        datetime.timezone.utc).isoformat(timespec="seconds")
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    total_days = 0
    for s in STATIONS:
        days = {}
        for ymd in dates:
            try:
                ev = fetch_day(s["code"], ymd)
                if ev:
                    days[ymd] = ev
            except Exception as ex:  # noqa: BLE001 - 부분 실패 허용
                print(f"WARN {s['code']} {ymd}: {ex}", file=sys.stderr)
            time.sleep(0.1)  # 완만한 호출
        (data_dir / f"{s['code']}.json").write_text(
            json.dumps({
                "station": s["code"],
                "name": s["name"],
                "generated": gen,
                "days": days,
            }, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        total_days += len(days)
        print(f"OK {s['code']} {s['name']} ({len(days)} days)")

    (data_dir / "manifest.json").write_text(
        json.dumps({
            "generated": gen,
            "window": [dates[0], dates[-1]],
            "stations": [s["code"] for s in STATIONS],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"DONE {len(STATIONS)} stations, {total_days} station-days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
