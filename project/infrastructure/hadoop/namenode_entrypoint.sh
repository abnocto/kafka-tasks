#!/bin/bash

if [ ! -d "/hadoop/dfs/name/current" ]; then
  echo "Formatting namenode..."
  hdfs namenode -format -force -nonInteractive
fi

exec "$@"

