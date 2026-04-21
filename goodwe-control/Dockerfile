ARG BUILD_FROM
FROM ${BUILD_FROM}

COPY goodwe-control/run.sh /
RUN chmod a+x /run.sh

COPY custom_components/goodwe_battery_control/ /opt/goodwe_battery_control/

CMD [ "/run.sh" ]
