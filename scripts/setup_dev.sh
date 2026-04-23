#!/bin/bash
# Setup development environment for Huan Commerce Platform

set -e

echo "🚀 Setting up Huan Commerce Platform..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy .env from example
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Edit .env with your configuration"
fi

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate

# Create superuser
echo "👤 Creating superuser..."
python manage.py createsuperuser

# Create demo data (optional)
read -p "Create demo data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py shell < scripts/seed_data.py
fi

# Run tests
echo "✅ Running tests..."
pytest tests/

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run: python manage.py runserver"
echo "  3. Visit: http://localhost:8000/admin"
