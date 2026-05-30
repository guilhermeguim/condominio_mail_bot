FROM python:3.11-slim

# Keep Python from generating .pyc files inside the container and make logs
# flush immediately so Cloud Run and local containers show output in real time.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Every subsequent instruction runs from /app, which keeps file copies and the
# final startup command predictable regardless of the base image defaults.
WORKDIR /app

# Copy the dependency manifest before the application code. That way Docker can
# reuse the installed dependency layer when only source files change.
COPY requirements.txt ./

# Install everything into the image without preserving pip's download cache,
# which helps keep the final runtime image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# The application itself is small, so copying the entire src directory is enough
# to make the FastAPI entrypoint and helper modules available at runtime.
COPY ./src ./src

# Cloud Run maps incoming traffic to port 8080 by default, so the image makes
# that contract explicit here.
EXPOSE 8080

# Uvicorn boots the FastAPI app directly from src.main and listens on all
# interfaces so the container runtime can reach it.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]