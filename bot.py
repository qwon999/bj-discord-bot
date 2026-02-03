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

    def send_discord(self, sub):
        problem_url = f"https://www.acmicpc.net/problem/{sub['problem_id']}"

        embed = {
            "title": "🎉 맞았습니다!",
            "color": 0x00FF00,
            "fields": [
                {"name": "👤 유저", "value": sub["username"], "inline": True},
                {
                    "name": "📝 문제",
                    "value": f"[{sub['problem_id']}. {sub['problem_title']}]({problem_url})",
                    "inline": True
                },
                {"name": "💻 언어", "value": sub["language"], "inline": True},
                {"name": "⏱️ 실행시간", "value": sub["time"] or "-", "inline": True},
                {"name": "💾 메모리", "value": sub["memory"] or "-", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        r = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        if r.status_code == 204:
            print(f"[{datetime.now()}] 알림 전송: {sub['username']} - {sub['problem_title']}")
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
