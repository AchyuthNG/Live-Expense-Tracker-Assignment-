# Stage 1 — build the Vite production bundle
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# Embed the API base at build time so the static bundle knows where to call.
ARG VITE_API_BASE=http://localhost:8000/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# Stage 2 — serve the static bundle via nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]