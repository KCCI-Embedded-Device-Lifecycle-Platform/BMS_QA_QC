#!/usr/bin/env bash
set -eu

# Collect reproducible, non-secret environment evidence for BEOG-92.
# This script is deliberately read-only: it does not configure CAN, flash an ECU,
# actuate a relay, or print GitLab Runner configuration/tokens.

output_dir="${1:-reports/portfolio/$(date -u +%Y%m%dT%H%M%SZ)}"
can_channel="${CAN_CHANNEL:-can0}"

mkdir -p "$output_dir"

record() {
    name="$1"
    shift
    {
        printf 'command:'
        printf ' %q' "$@"
        printf '\n\n'
        "$@"
    } >"$output_dir/$name.txt" 2>&1 || true
}

{
    printf 'captured_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'qa_commit=%s\n' "$(git rev-parse HEAD 2>/dev/null || printf unavailable)"
    printf 'qa_branch=%s\n' "$(git branch --show-current 2>/dev/null || printf unavailable)"
    printf 'ci_pipeline_url=%s\n' "${CI_PIPELINE_URL:-local}"
    printf 'ci_job_url=%s\n' "${CI_JOB_URL:-local}"
    printf 'can_channel=%s\n' "$can_channel"
} >"$output_dir/identity.txt"

record os uname -a
if command -v hostnamectl >/dev/null 2>&1; then
    record host hostnamectl
fi
record git-status git status --short --branch
record git-remotes git remote -v

for tool in python3 gcc arm-none-eabi-gcc docker gitlab-runner; do
    if command -v "$tool" >/dev/null 2>&1; then
        case "$tool" in
            python3) record tool-python python3 --version ;;
            gcc) record tool-gcc gcc --version ;;
            arm-none-eabi-gcc) record tool-arm-gcc arm-none-eabi-gcc --version ;;
            docker) record tool-docker docker version ;;
            gitlab-runner) record tool-gitlab-runner gitlab-runner --version ;;
        esac
    fi
done

if command -v ip >/dev/null 2>&1 && ip link show "$can_channel" >/dev/null 2>&1; then
    record can-interface ip -details -statistics link show "$can_channel"
elif [ -e /dev/ttyUSB0 ]; then
    record can-usb ls -l /dev/ttyUSB0
else
    printf 'BLOCKED_INFRA: neither %s nor /dev/ttyUSB0 is present\n' "$can_channel" \
        >"$output_dir/can-interface.txt"
fi

if command -v sha256sum >/dev/null 2>&1 && [ -d reports ]; then
    find reports -type f \( -name 'junit.xml' -o -name 'metadata.json' -o -name 'manifest.json' \) \
        -exec sha256sum {} \; >"$output_dir/report-sha256.txt" 2>&1 || true
fi

if command -v sha256sum >/dev/null 2>&1; then
    find "$output_dir" -maxdepth 1 -type f ! -name SHA256SUMS -exec sha256sum {} \; \
        >"$output_dir/SHA256SUMS"
fi

printf 'Evidence written to %s\n' "$output_dir"
