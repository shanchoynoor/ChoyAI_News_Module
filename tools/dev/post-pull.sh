#!/bin/bash

# Post-pull hook for automatic cache clearing
# Place this in your server's .git/hooks/post-merge

echo "🔄 Post-pull operations starting..."

# Clear application caches
echo "🗑️  Clearing application caches..."
rm -rf data/cache/*.json 2>/dev/null || true
rm -rf data/memory.json 2>/dev/null || true

# If running in Docker, restart the container
if command -v docker-compose > /dev/null 2>&1; then
    echo "🐳 Restarting Docker container..."
    docker-compose restart choynews-bot
fi

echo "✅ Post-pull operations complete!"
