import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# 설정
GROUP_ID = os.environ.get("GROUP_ID", "23427")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))
LAST_ID_FILE = "/data/last_submission_id.txt"

# 🔑 BOJ 자동 로그인 쿠키
BOJ_AUTOLOGIN = os.environ.get(
    "BOJ_AUTOLOGIN",
    ""
)

class BOJMonitor:
    # 티어별 색상 및 이름
    TIER_INFO = {
        0: {"name": "Unrated", "color": 0x2D2D2D},
        1: {"name": "Bronze V", "color": 0xAD5600},
        2: {"name": "Bronze IV", "color": 0xAD5600},
        3: {"name": "Bronze III", "color": 0xAD5600},
        4: {"name": "Bronze II", "color": 0xAD5600},
        5: {"name": "Bronze I", "color": 0xAD5600},
        6: {"name": "Silver V", "color": 0x435F7A},
        7: {"name": "Silver IV", "color": 0x435F7A},
        8: {"name": "Silver III", "color": 0x435F7A},
        9: {"name": "Silver II", "color": 0x435F7A},
        10: {"name": "Silver I", "color": 0x435F7A},
        11: {"name": "Gold V", "color": 0xEC9A00},
        12: {"name": "Gold IV", "color": 0xEC9A00},
        13: {"name": "Gold III", "color": 0xEC9A00},
        14: {"name": "Gold II", "color": 0xEC9A00},
        15: {"name": "Gold I", "color": 0xEC9A00},
        16: {"name": "Platinum V", "color": 0x27E2A4},
        17: {"name": "Platinum IV", "color": 0x27E2A4},
        18: {"name": "Platinum III", "color": 0x27E2A4},
        19: {"name": "Platinum II", "color": 0x27E2A4},
        20: {"name": "Platinum I", "color": 0x27E2A4},
        21: {"name": "Diamond V", "color": 0x00B4FC},
        22: {"name": "Diamond IV", "color": 0x00B4FC},
        23: {"name": "Diamond III", "color": 0x00B4FC},
        24: {"name": "Diamond II", "color": 0x00B4FC},
        25: {"name": "Diamond I", "color": 0x00B4FC},
        26: {"name": "Ruby V", "color": 0xFF0062},
        27: {"name": "Ruby IV", "color": 0xFF0062},
        28: {"name": "Ruby III", "color": 0xFF0062},
        29: {"name": "Ruby II", "color": 0xFF0062},
        30: {"name": "Ruby I", "color": 0xFF0062},
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

        # 🔥 쿠키로 로그인 처리
        self.session.cookies.set(
            "bojautologin",
            BOJ_AUTOLOGIN,
            domain=".acmicpc.net",
            path="/"
        )

        self.last_submission_id = self.load_last_id()

    def load_last_id(self):
        if os.path.exists(LAST_ID_FILE):
            with open(LAST_ID_FILE, "r") as f:
                return int(f.read().strip())
        return 0

    def save_last_id(self):
        os.makedirs(os.path.dirname(LAST_ID_FILE), exist_ok=True)
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(self.last_submission_id))

    def get_status(self):
        url = f"https://www.acmicpc.net/status?group_id={GROUP_ID}"
        response = self.session.get(url)

        # 로그인 실패 감지
        if "로그인" in response.text:
            print(f"[{datetime.now()}] ❌ 인증 실패 (쿠키 만료 가능)")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "status-table"})
        if not table:
            print(f"[{datetime.now()}] 상태 테이블 없음")
            return []

        submissions = []
        rows = table.find("tbody").find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 9:
                continue

            submission_id = int(cols[0].text.strip())
            username = cols[1].text.strip()

            problem_link = cols[2].find("a")
            if not problem_link:
                continue

            problem_id = problem_link["href"].split("/")[-1]
            problem_title = problem_link.text.strip()

            result = cols[3].text.strip()
            memory = cols[4].text.strip()
            exec_time = cols[5].text.strip()
            language = cols[6].text.strip()

            submissions.append({
                "id": submission_id,
                "username": username,
                "problem_id": problem_id,
                "problem_title": problem_title,
                "result": result,
                "memory": memory,
                "time": exec_time,
                "language": language
            })

        return submissions

    def get_problem_info(self, problem_id):
        """solved.ac API에서 문제 정보 가져오기"""
        try:
            url = f"https://solved.ac/api/v3/problem/show?problemId={problem_id}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "level": data.get("level", 0),
                    "title": data.get("titleKo", f"문제 {problem_id}")
                }
            return {"level": 0, "title": f"문제 {problem_id}"}
        except Exception as e:
            print(f"[{datetime.now()}] solved.ac API 오류: {e}")
            return {"level": 0, "title": f"문제 {problem_id}"}

    def send_discord(self, sub):
        problem_url = f"https://www.acmicpc.net/problem/{sub['problem_id']}"
        submission_url = f"https://www.acmicpc.net/status?problem_id={sub['problem_id']}&user_id={sub['username']}"

        # 문제 정보 가져오기 (난이도 + 제목)
        problem_info = self.get_problem_info(sub['problem_id'])
        tier_info = self.TIER_INFO.get(problem_info['level'], self.TIER_INFO[0])
        problem_title = problem_info['title']

        # 메모리와 시간 정보 포맷팅
        footer_text = f"{sub['language']}"
        if sub['time']:
            footer_text += f" • {sub['time']}"
        if sub['memory']:
            footer_text += f" • {sub['memory']}"

        embed = {
            "title": f"✨ {sub['username']}님이 문제를 해결했습니다!",
            "description": f"**[{sub['problem_id']}. {problem_title}]({problem_url})**\n난이도: **{tier_info['name']}**",
            "color": tier_info['color'],
            "footer": {
                "text": footer_text
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        r = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        if r.status_code == 204:
            print(f"[{datetime.now()}] 알림 전송: {sub['username']} - {problem_title} ({tier_info['name']})")
        else:
            print(f"[{datetime.now()}] 디스코드 실패: {r.status_code}")

    def check_and_notify(self):
        submissions = self.get_status()
        max_id = self.last_submission_id
        new_accepted = []

        for sub in submissions:
            if sub["id"] <= self.last_submission_id:
                continue

            max_id = max(max_id, sub["id"])

            if "맞았습니다" in sub["result"]:
                new_accepted.append(sub)

        for sub in reversed(new_accepted):
            self.send_discord(sub)
            time.sleep(1)

        if max_id > self.last_submission_id:
            self.last_submission_id = max_id
            self.save_last_id()

    def run(self):
        print(f"[{datetime.now()}] 🚀 BOJ 그룹 알림봇 시작")
        print(f"Group ID: {GROUP_ID}")

        while True:
            try:
                self.check_and_notify()
            except Exception as e:
                print(f"[{datetime.now()}] 에러: {e}")

            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    BOJMonitor().run()
