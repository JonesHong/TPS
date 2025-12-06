#!/bin/bash

# Get the absolute path to the project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "Starting TPS Development Environment..."

# Command for Backend
BACKEND_CMD="uv run uvicorn tps.app:app --reload"

# Command for Frontend
FRONTEND_CMD="pnpm dev"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS"
    osascript -e "tell application \"Terminal\" to do script \"cd '$ROOT_DIR' && $BACKEND_CMD\""
    osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_DIR' && $FRONTEND_CMD\""
else
    # Linux
    echo "Detected Linux"
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --working-directory="$ROOT_DIR" -- bash -c "$BACKEND_CMD; exec bash"
        gnome-terminal --working-directory="$FRONTEND_DIR" -- bash -c "$FRONTEND_CMD; exec bash"
    elif command -v konsole &> /dev/null; then
        konsole --workdir "$ROOT_DIR" -e bash -c "$BACKEND_CMD; exec bash" &
        konsole --workdir "$FRONTEND_DIR" -e bash -c "$FRONTEND_CMD; exec bash" &
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$ROOT_DIR' && $BACKEND_CMD; exec bash" &
        xterm -e "cd '$FRONTEND_DIR' && $FRONTEND_CMD; exec bash" &
    else
        echo "Could not detect a supported terminal emulator (gnome-terminal, konsole, xterm)."
        echo "Running processes in the background..."
        # Function to kill background processes on exit
        cleanup() {
            echo "Stopping processes..."
            kill $BACKEND_PID $FRONTEND_PID
        }
        trap cleanup EXIT

        (cd "$ROOT_DIR" && $BACKEND_CMD) &
        BACKEND_PID=$!
        (cd "$FRONTEND_DIR" && $FRONTEND_CMD) &
        FRONTEND_PID=$!
        
        wait
    fi
fi
