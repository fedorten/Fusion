.PHONY: help install backend frontend dev docker-up docker-down clean explore setup-backend setup-frontend

# Путь к uv (можно переопределить через переменную окружения)
UV ?= uv
PYTHON ?= python3

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup-backend - Setup backend virtual environment with uv"
	@echo "  make setup-frontend - Install frontend dependencies"
	@echo "  make install       - Install all dependencies (backend + frontend)"
	@echo "  make backend       - Run backend server only"
	@echo "  make frontend      - Run frontend dev server only"
	@echo "  make dev           - Run both backend and frontend"
	@echo "  make docker-up     - Start with Docker Compose"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make clean         - Clean up temporary files"

# Setup backend virtual environment
setup-backend:
	@echo "Setting up backend virtual environment with uv..."
	cd backend && $(UV) venv
	@echo "Installing backend dependencies..."
	cd backend && $(UV) pip install -e .

# Setup frontend dependencies
setup-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Install all dependencies
install: setup-backend setup-frontend
	@echo "All dependencies installed!"

# Run backend with uv
backend:
	@echo "Starting backend server on http://localhost:8000"
	@echo "API docs: http://localhost:8000/docs"
	@echo "WebSocket: ws://localhost:8000/api/v1/ws/{chat_id}"
	@if [ ! -d "backend/.venv" ]; then \
		echo "Virtual environment not found. Running setup-backend first..."; \
		$(MAKE) setup-backend; \
	fi
	cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend
frontend:
	@echo "Starting frontend dev server..."
	@echo "Frontend will be available at the URL shown below (usually http://localhost:5173)"
	cd frontend && npm run dev

# Run both backend and frontend in parallel
dev:
	@echo "Starting both backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173 (or check the output below)"
	@echo "API docs: http://localhost:8000/docs"
	@echo "Press Ctrl+C to stop both servers"
	@if [ ! -d "backend/.venv" ]; then \
		echo "Virtual environment not found. Running setup-backend first..."; \
		$(MAKE) setup-backend; \
	fi
	@trap 'kill 0' EXIT; \
	cd backend && . .venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"