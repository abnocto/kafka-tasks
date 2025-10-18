    #!/bin/bash
    set -e

    mkdir -p /usr/local/hadoop/hdfs/namenode
    chmod -R 777 /usr/local/hadoop/hdfs/namenode

    if [ ! -f /usr/local/hadoop/hdfs/namenode/current/VERSION ]; then
        echo "Форматирование NameNode..."
        hdfs namenode -format -nonInteractive
    else
        echo "NameNode уже отформатирован, пропускаем форматирование"
    fi
    
    exec "$@"
    