FROM node:latest as build
WORKDIR /fmtm_openlayer_map
COPY package.json .
RUN npm install
COPY . .
RUN npm run build
FROM nginx:latest
COPY --from=build  /fmtm_openlayer_map/dist /usr/share/nginx/html
