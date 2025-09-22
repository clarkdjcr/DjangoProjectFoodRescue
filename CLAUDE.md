# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django 5.2.6 project in its initial setup phase. The project follows standard Django conventions with a clean, minimal structure.

## Project Structure

```
DjangoProject/
├── DjangoProject/          # Main Django project package
│   ├── settings.py         # Django settings configuration
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── templates/             # Django templates directory (currently empty)
├── manage.py              # Django management script
└── .venv/                # Virtual environment
```

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # (if requirements.txt exists)
```

### Django Management
```bash
# Run development server
python manage.py runserver

# Run database migrations
python manage.py migrate

# Create new migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run Django shell
python manage.py shell

# Run tests
python manage.py test
```

## Configuration

- **Database**: SQLite3 (default Django configuration)
- **Debug Mode**: Enabled (development setting)
- **Templates Directory**: `templates/` (configured but empty)
- **Static Files**: Standard Django static files setup
- **Time Zone**: UTC
- **Secret Key**: Development key (should be changed for production)

## Architecture Notes

- Standard Django project layout with no custom apps yet
- Uses Django's built-in admin interface (accessible at `/admin/`)
- Templates directory is configured but currently empty
- No custom apps or models have been created yet
- Virtual environment is set up with minimal Django dependencies

## Dependencies

- Django 5.2.6
- asgiref 3.9.1
- sqlparse 0.5.3