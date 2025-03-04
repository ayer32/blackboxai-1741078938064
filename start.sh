#!/bin/bash

# Start backend services
echo "Starting backend services..."
docker-compose up -d

# Wait for backend services to be ready
echo "Waiting for backend services to be ready..."
sleep 10

# Start Flutter app
echo "Starting Flutter app..."
cd mobile
flutter pub get
flutter run -d chrome --web-port 3000

# Note: To run on mobile devices:
# For Android: flutter run -d android
# For iOS: flutter run -d ios
