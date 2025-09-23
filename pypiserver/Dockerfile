FROM pypiserver/pypiserver:latest

RUN apk add apache2-utils

RUN htpasswd -c -b /.htpasswd admin admin

WORKDIR /

CMD ["run","-a","update","-P","/.htpasswd","--overwrite","/data/packages/"]