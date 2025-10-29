FROM bitnamilegacy/kafka:3.4

USER root

COPY mm2.properties /opt/bitnami/kafka/config/mm2.properties

USER 1001

CMD ["/opt/bitnami/kafka/bin/connect-mirror-maker.sh", "/opt/bitnami/kafka/config/mm2.properties"]
