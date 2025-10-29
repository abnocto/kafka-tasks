#!/bin/bash

echo "Waiting for namenode..."
until hdfs dfsadmin -safemode get 2>/dev/null | grep -q "Safe mode is"; do
  sleep 2
done

exec "$@"

