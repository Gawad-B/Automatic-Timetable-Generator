FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json package-lock.json tsconfig.json ./
COPY static/js/app.ts ./static/js/app.ts
RUN npm ci && npm run build

FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-build /app/static/js/app.js /app/static/js/app.js

RUN mkdir -p static/uploads/courses static/uploads/instructors static/uploads/rooms static/uploads/timeslots static/uploads/sections

EXPOSE 5000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
