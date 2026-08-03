#!/bin/sh
if [ -z "$API_ENDPOINT" ]; then
  echo "API_ENDPOINT is required" >&2
  exit 1
fi
exit 0
