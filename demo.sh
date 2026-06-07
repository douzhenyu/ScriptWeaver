#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:8137"
JOB="demo-001"
BOLD="\033[1m"
GREEN="\033[32m"
RESET="\033[0m"

step() { echo -e "\n${BOLD}=== $1 ===${RESET}"; }

step "1. Health check"
curl -fsS "$BASE/health" | python3 -m json.tool

step "2. Create job"
curl -fsS -X POST "$BASE/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"job_id\": \"$JOB\"}" | python3 -m json.tool

step "3. Upload 3 chapters"
curl -fsS -X POST "$BASE/jobs/$JOB/chapters" \
  -H "Content-Type: application/json" \
  -d '{
  "chapters": [
    {"index":1,"title":"第一章","content":"林照收到父亲留下的密信，决心调查真相。"},
    {"index":2,"title":"第二章","content":"沈微突然出现，警告林照不要公开密信内容。"},
    {"index":3,"title":"第三章","content":"两人发现密信指向二十年前的旧案，决定联手调查。"}
  ]
}' | python3 -m json.tool

step "4. Generate AI analysis"
curl -fsS -X POST "$BASE/jobs/$JOB/analyze" | python3 -m json.tool

step "5. Answer uncertainty"
UNCERTAINTY=$(curl -fsS "$BASE/jobs/$JOB/next-uncertainty")
echo "$UNCERTAINTY" | python3 -m json.tool
UNC_ID=$(echo "$UNCERTAINTY" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -fsS -X POST "$BASE/jobs/$JOB/uncertainty-answer" \
  -H "Content-Type: application/json" \
  -d "{\"uncertainty_id\": \"$UNC_ID\", \"selected_option_id\": \"option_001\"}" | python3 -m json.tool

step "6. Confirm analysis"
curl -fsS -X POST "$BASE/jobs/$JOB/confirm-analysis" | python3 -m json.tool

step "7. Generate & confirm plan"
curl -fsS -X POST "$BASE/jobs/$JOB/generate-plan" | python3 -m json.tool
curl -fsS -X POST "$BASE/jobs/$JOB/confirm-plan" \
  -H "Content-Type: application/json" \
  -d "$(curl -fsS "$BASE/jobs/$JOB" | python3 -c "
import sys,json
j=json.load(sys.stdin)
p=j['adaptation_plan']
print(json.dumps(p))
")" | python3 -m json.tool

step "8. Generate screenplay & export YAML"
curl -fsS -X POST "$BASE/jobs/$JOB/generate-screenplay" | python3 -m json.tool

echo -e "\n${GREEN}${BOLD}=== YAML Export ===${RESET}"
curl -fsS "$BASE/jobs/$JOB/export-yaml?title=密信&author=测试作者"

echo -e "\n\n${GREEN}${BOLD}Demo complete.${RESET}"
