#!/bin/sh
if [ -z "$API_KEY" ]; then
  echo "API_KEY is required" >&2
  exit 1
fi
exit 0
