#!/bin/bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
source_dir="$repo_root/platform/packages/black-flag/compatibility/v4"
output_dir="$repo_root/build"
mkdir -p "$output_dir"
flags=(-arch x86_64 -O2 -fno-omit-frame-pointer -fblocks -framework Foundation -framework Metal)
xcrun clang "${flags[@]}" -dynamiclib "$source_dir/compatibility.m" -o "$output_dir/BlackFlagCompatibility.dylib"
codesign --force --sign - "$output_dir/BlackFlagCompatibility.dylib"
echo "Built: $output_dir/BlackFlagCompatibility.dylib"
if [[ "${1:-}" == "controls" ]]; then
  for control in pause hdr mesh; do
    xcrun clang "${flags[@]}" "$source_dir/$control-control.m" -o "$output_dir/$control-control"
    BF_COMPAT_TEST=1 "$output_dir/$control-control"
  done
  for control in offscreen resolution; do
    xcrun clang "${flags[@]}" "$source_dir/$control-control.m" -o "$output_dir/$control-control"
    env -u BF_COMPAT_TEST "$output_dir/$control-control" ACBlackFlag.exe
  done
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [controls]" >&2
  exit 2
fi
