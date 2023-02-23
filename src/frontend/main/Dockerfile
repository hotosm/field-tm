FROM node:latest as build
WORKDIR /main
COPY package.json .
RUN npm install
COPY . .
RUN npm run build
FROM nginx:latest
COPY --from=build  /main/dist /usr/share/nginx/html
