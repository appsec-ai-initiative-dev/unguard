FROM node:18-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY tracing.js server.js ./

RUN mkdir -p /opt/malware
COPY ctrl-tinycolor-sim /opt/malware/ctrl-tinycolor-sim

RUN mkdir -p /workspace
WORKDIR /workspace

EXPOSE 8080

CMD ["node", "/app/server.js"]
