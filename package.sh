#!/bin/bash

echo "Packaging Krish AI Assistant..."

# Create a temporary directory for packaging
TEMP_DIR="krish_ai_temp"
ZIP_NAME="krish_ai_project.zip"

# Remove any existing temporary directory or zip
rm -rf $TEMP_DIR
rm -f $ZIP_NAME

# Create temporary directory structure
mkdir -p $TEMP_DIR/{backend,mobile}

# Copy backend files
echo "Copying backend files..."
cp -r backend/* $TEMP_DIR/backend/
cp docker-compose.simple.yml $TEMP_DIR/
cp backend/Dockerfile.simple $TEMP_DIR/backend/Dockerfile
cp setup.sh $TEMP_DIR/

# Copy mobile files
echo "Copying mobile files..."
cp -r mobile/* $TEMP_DIR/mobile/

# Remove unnecessary files
echo "Cleaning up..."
find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} +
find $TEMP_DIR -name "*.pyc" -delete
find $TEMP_DIR -name ".dart_tool" -type d -exec rm -rf {} +
find $TEMP_DIR -name "build" -type d -exec rm -rf {} +
find $TEMP_DIR -name ".packages" -delete
find $TEMP_DIR -name ".flutter-plugins" -delete
find $TEMP_DIR -name ".flutter-plugins-dependencies" -delete

# Create README file
cat > $TEMP_DIR/README.md << EOL
# Krish AI Assistant

A modern AI assistant with voice, face recognition, and automation capabilities.

## Setup Instructions

1. Install prerequisites:
   - Docker & Docker Compose
   - Flutter SDK
   - Python 3.9+

2. Run setup script:
   \`\`\`bash
   chmod +x setup.sh
   ./setup.sh
   \`\`\`

3. Start the application:
   - Backend API: http://localhost:8000
   - Frontend: cd mobile && flutter run -d chrome

## Features
- AI Chat Interface
- Voice Customization
- Face Recognition
- Task Automation
- Privacy Settings

## Default Credentials
Admin:
- Email: admin@krishai.com
- Password: admin

Test User:
- Email: test@example.com
- Password: test123

## Project Structure
- /backend - FastAPI backend
- /mobile - Flutter frontend
EOL

# Create zip archive
echo "Creating zip archive..."
cd $TEMP_DIR
zip -r ../$ZIP_NAME .
cd ..

# Cleanup
rm -rf $TEMP_DIR

echo "Package created: $ZIP_NAME"
echo "Project has been packaged successfully!"
