FROM bitnamilegacy/kafka:3.4

USER root

RUN install_packages curl jq

COPY init.sh /init.sh

RUN chmod +x /init.sh

USER 1001

CMD ["/init.sh"]
