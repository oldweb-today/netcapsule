FROM nginx:latest

RUN usermod -u 1000 www-data
#RUN usermod -G staff www-data
#RUN chown -Rf www-data /cache
ADD nginx.conf /etc/nginx/nginx.conf
