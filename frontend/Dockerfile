# ══════════════════════════════════════════════════════════════════
# Dockerfile — Frontend (nginx serving dashboard.html)
# ══════════════════════════════════════════════════════════════════

FROM nginx:alpine

LABEL maintainer="emna"
LABEL description="5G+6G Network Slicing Dashboard Frontend"

# Copy dashboard
COPY dashboard.html /usr/share/nginx/html/dashboard.html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
