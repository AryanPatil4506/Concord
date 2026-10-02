# Hugging Face Space: builds the CONCORD console from the GitHub repo.
# After pushing to GitHub, use "Factory rebuild" in the Space settings to pick up the changes.
FROM alpine/git AS src
ARG REPO=https://github.com/AryanPatil4506/Concord.git
ARG REF=main
RUN git clone --depth 1 --branch ${REF} ${REPO} /src

FROM node:20-slim AS console
WORKDIR /app/console
COPY --from=src /src/prototype/console/package.json /src/prototype/console/package-lock.json ./
RUN npm ci
COPY --from=src /src/prototype/console/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY --from=src /src/prototype/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=src /src/prototype/ ./
COPY --from=console /app/console/dist ./console/dist
RUN rm -rf console/node_modules
ENV HOST=0.0.0.0 PORT=7860 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 7860
USER 1000
CMD ["python", "-m", "server"]
