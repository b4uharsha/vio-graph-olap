FROM nginx:1.27-alpine

LABEL maintainer="graph-olap-platform"

USER root

COPY entrypoint.sh /docker-entrypoint.sh
COPY nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /etc/nginx && \
    chmod -R 777 /etc/nginx && \
    mkdir -p /var/lib/nginx \
             /var/cache/nginx/client_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp && \
    chmod -R 777 /var/lib/nginx && \
    chmod -R 777 /var/cache/nginx && \
    chmod -R 777 /var/log/nginx && \
    chmod 755 /docker-entrypoint.sh

USER nginx

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
