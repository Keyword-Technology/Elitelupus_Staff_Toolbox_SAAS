FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directories for static files
RUN mkdir -p /var/www/static /var/www/media

# Expose ports
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
