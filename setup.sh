#!/bin/bash

echo "Setting up Krish AI Assistant..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "Flutter is not installed. Please install Flutter first."
    exit 1
fi

# Create necessary directories
echo "Creating project structure..."
mkdir -p backend/plugins
mkdir -p mobile/assets/{animations,images,icons,fonts}

# Copy environment variables template
echo "Setting up environment variables..."
cat > backend/.env << EOL
MONGODB_URL=mongodb://mongodb:27017/krishai
REDIS_URL=redis://redis:6379
JWT_SECRET=your-secret-key
OPENAI_API_KEY=your-openai-key
EOL

# Copy simplified Dockerfile
echo "Copying simplified Dockerfile..."
cp backend/Dockerfile.simple backend/Dockerfile

# Start Docker services
echo "Starting Docker services..."
docker-compose -f docker-compose.simple.yml up -d

# Install Flutter dependencies
echo "Setting up Flutter project..."
cd mobile
flutter pub get

# Back to root directory
cd ..

echo "Setup completed!"
echo "To start the application:"
echo "1. Backend API: http://localhost:8000"
echo "2. Frontend (run): cd mobile && flutter run -d chrome"

# Print status
echo -e "\nService Status:"
docker-compose -f docker-compose.simple.yml ps

echo -e "\nNext steps:"
echo "1. Update backend/.env with your API keys"
echo "2. Access API docs at http://localhost:8000/docs"
echo "3. Run Flutter app with: cd mobile && flutter run -d chrome"
