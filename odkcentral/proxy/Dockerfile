FROM docker.io/nginx:1.23-alpine as prod
WORKDIR /usr/share/nginx/html
# Remove default Nginx static assets
RUN rm -rf ./* /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf
COPY . /etc/nginx
