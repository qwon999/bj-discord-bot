# BOJ 그룹 디스코드 알림 봇

백준 그룹의 채점 현황을 모니터링하여 "맞았습니다" 판정을 받으면 디스코드로 알림을 보내는 봇입니다.

## 기능

- 그룹 채점 현황 주기적 모니터링 (기본 60초)
- "맞았습니다" 판정만 필터링
- 디스코드 웹훅으로 알림 전송
- 중복 알림 방지 (제출 번호 저장)

## 알림 내용

- 유저명
- 문제번호 + 문제이름 (링크 포함)
- 언어
- 실행시간
- 메모리

## 사용법

### 라즈베리파이에서 실행

1. 파일 복사
```bash
scp -r boj-discord-bot pi@라즈베리파이주소:~/
```

2. 환경 설정
```bash
cd boj-discord-bot
cp docker-compose.yml.example docker-compose.yml
# docker-compose.yml 파일을 열어서 환경변수 수정
```

3. 실행
```bash
docker compose up -d
```

3. 로그 확인
```bash
docker compose logs -f
```

4. 중지
```bash
docker compose down
```

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| BOJ_AUTOLOGIN | 백준 자동 로그인 쿠키 | - |
| GROUP_ID | 그룹 ID | 23427 |
| WEBHOOK_URL | 디스코드 웹훅 URL | - |
| POLL_INTERVAL | 폴링 간격 (초) | 60 |

## 데이터

`./data/last_submission_id.txt`에 마지막으로 확인한 제출 번호가 저장됩니다.
컨테이너를 재시작해도 중복 알림이 가지 않습니다.
