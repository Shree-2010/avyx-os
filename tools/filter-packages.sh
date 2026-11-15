#!/bin/bash
# Drop package names that do not exist in the configured apt sources, and record them.
# A single misspelt or renamed package would otherwise abort a 30-minute build.
# Usage: filter-packages.sh <dropped-report-file> <list-file>...
set -euo pipefail

report="$1"; shift
: > "$report"

for f in "$@"; do
  tmp="$(mktemp)"
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|'#'*) printf '%s\n' "$line" >> "$tmp"; continue ;;
    esac
    keep=()
    for pkg in $line; do
      if apt-cache show "$pkg" >/dev/null 2>&1; then
        keep+=("$pkg")
      else
        echo "$pkg  (from $(basename "$f"))" >> "$report"
        echo "filter-packages: dropping unavailable package: $pkg" >&2
      fi
    done
    if [ "${#keep[@]}" -gt 0 ]; then printf '%s\n' "${keep[*]}" >> "$tmp"; fi
  done < "$f"
  mv "$tmp" "$f"
done
