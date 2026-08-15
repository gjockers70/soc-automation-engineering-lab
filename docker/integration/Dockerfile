FROM soc-integration-gateway:phase12
USER 0:0
RUN rm -rf /app/src
COPY src /app/src
COPY operations/failure-lab /app/failure-lab
USER 10001:10001
