# Build and run the board-manager Copilot Extension on Azure Container Apps
# or any Docker-compatible host.
#
# Azure Container Apps (recommended):
#   az containerapp up \
#     --name board-manager \
#     --resource-group YOUR_RG \
#     --image board-manager \
#     --env-vars GITHUB_OWNER=... PROJECT_NUMBER=... GITHUB_REPO=...
#
# Local:
#   docker build -t board-manager .
#   docker run -p 3000:3000 --env-file .env board-manager

FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
EXPOSE 3000
CMD ["node", "server.js"]
