#!/usr/bin/env bash
# Stage the unreleased June 2025 1C/2C review pack privately on production.
set -Eeuo pipefail

usage() {
  echo "Usage: $0 --dry-run|--execute '/absolute/path/to/June 2025 source folder'" >&2
  exit 2
}
[[ $# -eq 2 ]] || usage
mode="$1"
source_root="$2"
[[ "$mode" == --dry-run || "$mode" == --execute ]] || usage
[[ -d "$source_root/.pilot-review/question-pages" && -d "$source_root/.pilot-review/scheme-pages" ]] || usage
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
connector="${script_dir}/../../deploy/server/connect-vm2"
bank="${source_root}/.pilot-review/june-2025-standard-draft-bank.json"
[[ -f "$bank" ]] || usage

python3 - "$bank" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
bank = json.loads(p.read_text())
assert bank.get('status') == 'local_draft_unreleased'
assert bank.get('studentAccess') is False
assert [(row['component'], row['variant']) for row in bank['papers']] == [('1C', 'standard'), ('2C', 'standard')]
assert len(bank['questions']) == 16
assert all(question['studentPrompt'] is None and not question['topicMappings'] for question in bank['questions'])
print(f"Validated unreleased bank: {len(bank['questions'])} questions")
PY

checksum="$(shasum -a 256 "$bank" | awk '{print $1}')"
remote_base="/data/akuru/pilots/pearson-chemistry-june-2025-standard"
echo "Private destination: $remote_base"
echo "Draft bank SHA-256: $checksum"
if [[ "$mode" == --dry-run ]]; then
  echo "Dry run complete; no production changes made."
  exit 0
fi

# A fresh destination prevents silent replacement of an earlier analysis pack.
"$connector" "sudo test ! -e '$remote_base' && sudo install -d -o akuru -g akuru -m 0700 '/data/akuru/pilots' && sudo install -d -o akuru -g akuru -m 0700 '$remote_base'"
COPYFILE_DISABLE=1 tar -C "$source_root" -cf - .pilot-review/june-2025-standard-draft-bank.json .pilot-review/question-pages .pilot-review/scheme-pages |
  "$connector" "sudo -u akuru tar -C '$remote_base' -xf -"
cat "$script_dir/analyze-staged-pearson-chemistry.py" |
  "$connector" "sudo -u akuru tee '$remote_base/analyze-staged-pearson-chemistry.py' >/dev/null"
"$connector" "sudo -u akuru bash -c 'set -Eeuo pipefail; cd /opt/akuru/source-code/backend; export PYTHONPATH=/opt/akuru/source-code/backend; /opt/akuru/source-code/backend/.venv/bin/python '$remote_base'/analyze-staged-pearson-chemistry.py '$remote_base'/.pilot-review/june-2025-standard-draft-bank.json --output '$remote_base'/analysis-report.json' && sudo find '$remote_base' -type f -exec chmod 0600 {} + && sudo find '$remote_base' -type d -exec chmod 0700 {} +"
remote_checksum="$("$connector" "sudo -u akuru sha256sum '$remote_base/.pilot-review/june-2025-standard-draft-bank.json'" | awk '{print $1}')"
[[ "$remote_checksum" == "$checksum" ]] || { echo "Remote draft bank checksum mismatch" >&2; exit 1; }
echo "Verified matching remote SHA-256. The analysis report is private and no AKURU database rows were created."
