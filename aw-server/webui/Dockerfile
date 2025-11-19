FROM nginx:alpine

# Create web root directory with placeholder
# Note: dist will be mounted as volume in docker-compose.yml, overriding this
RUN mkdir -p /usr/share/nginx/html && \
    echo '<!DOCTYPE html><html><head><title>ActivityWatch - Building</title></head><body><h1>WebUI Building...</h1><p>Please build the webui: cd activitywatch/aw-server-rust/aw-webui && npm install && npm run build</p></body></html>' > /usr/share/nginx/html/index.html

# Copy built frontend if dist directory exists
COPY dist /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create nginx user if needed
RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

