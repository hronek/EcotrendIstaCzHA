ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    chromium-chromedriver \
    font-noto \
    font-noto-cjk \
    && rm -rf /var/cache/apk/*

# Create virtual environment and install Python packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --no-cache-dir \
    flask \
    selenium \
    pillow \
    requests

# Copy application
COPY run.sh /
COPY screenshot_server.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
