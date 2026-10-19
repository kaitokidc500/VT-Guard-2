# VT-Guard Buoc 9 - image offline (kieu A, docs/STEP9-BRIEF.md muc 6). Build tu context do docker/stage.py dung (docker/build/):
#   python docker/stage.py && docker build --platform linux/amd64 -t vtguard:step9 docker/build
# Khong chua log tho (ngoai log mau replay), checkpoint .pt hay thong tin dang nhap; khong can Internet khi chay.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VTGUARD_HOME=/app STREAMLIT_BROWSER_GATHER_USAGE_STATS=false TZ=UTC

WORKDIR /app
COPY docker/requirements.lock /tmp/requirements.lock
RUN pip install -r /tmp/requirements.lock && pip freeze > /app.freeze.txt

COPY . /app
RUN sed -i 's/\r$//' /app/docker/entrypoint.sh && chmod +x /app/docker/entrypoint.sh \
    && mv /app.freeze.txt /app/docker/requirements.freeze.txt \
    && useradd -m -u 1000 vtguard && chown -R vtguard /app/reports/step9
USER vtguard

EXPOSE 8501
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["dashboard"]
