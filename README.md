# ChatNova - Real-Time Messaging Application

A production-grade real-time messaging platform built with Django, React, WebSockets, and Redis. Supports direct messages, group chats, channels, threads, file sharing, emoji reactions, typing indicators, online presence, message search, and pinned messages.

## Architecture

```
                        +-------------------+
                        |   Nginx (Reverse  |
                        |      Proxy)       |
                        +--------+----------+
                                 |
                  +--------------+--------------+
                  |                             |
         +--------v--------+          +--------v--------+
         |  React Frontend |          |  Django Backend  |
         |  (Port 3000)    |          |  (Port 8000)     |
         +-----------------+          +--------+---------+
                                               |
                          +--------------------+--------------------+
                          |                    |                    |
                 +--------v------+    +--------v------+   +--------v------+
                 |  PostgreSQL   |    |    Redis       |   |    Celery      |
                 |  (Port 5432)  |    |  (Port 6379)  |   |   (Workers)    |
                 +---------------+    +---------------+   +---------------+
```

## Features

- **Direct Messages**: Private one-on-one messaging with read receipts
- **Group Chats**: Multi-user chat rooms with admin controls
- **Channels**: Public/private channels with topic management
- **Threads**: Threaded replies to keep conversations organized
- **File Sharing**: Upload and share images, documents, and media
- **Emoji Reactions**: React to messages with emoji
- **Typing Indicators**: Real-time typing status display
- **Online Presence**: See who is online, away, or offline
- **Message Search**: Full-text search across all conversations
- **Pinned Messages**: Pin important messages for quick reference
- **Notifications**: Real-time push notifications with preferences
- **User Profiles**: Customizable profiles with avatars and status

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Backend     | Django 5.x, Django REST Framework |
| WebSockets  | Django Channels, Daphne           |
| Frontend    | React 18, Redux Toolkit           |
| Database    | PostgreSQL 16                     |
| Cache/Queue | Redis 7                           |
| Task Queue  | Celery 5                          |
| Proxy       | Nginx                             |
| Container   | Docker, Docker Compose            |

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/chatnova.git
cd chatnova
```

2. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Build and start all services:
```bash
docker-compose up --build
```

4. Run database migrations:
```bash
docker-compose exec backend python manage.py migrate
```

5. Create a superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. Access the application:
- Frontend: http://localhost
- Backend API: http://localhost/api/
- Admin Panel: http://localhost/admin/
- API Docs: http://localhost/api/docs/

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm test
```

## API Endpoints

### Authentication
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| POST   | /api/auth/register/       | Register new user    |
| POST   | /api/auth/login/          | Login                |
| POST   | /api/auth/logout/         | Logout               |
| POST   | /api/auth/token/refresh/  | Refresh JWT token    |
| GET    | /api/auth/me/             | Get current user     |

### Conversations
| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| GET    | /api/conversations/               | List conversations       |
| POST   | /api/conversations/               | Create conversation      |
| GET    | /api/conversations/{id}/          | Get conversation detail  |
| POST   | /api/conversations/{id}/members/  | Add member               |
| DELETE | /api/conversations/{id}/members/  | Remove member            |

### Messages
| Method | Endpoint                              | Description          |
|--------|---------------------------------------|----------------------|
| GET    | /api/messages/{conversation_id}/      | List messages        |
| POST   | /api/messages/{conversation_id}/      | Send message         |
| PUT    | /api/messages/{id}/                   | Edit message         |
| DELETE | /api/messages/{id}/                   | Delete message       |
| POST   | /api/messages/{id}/reactions/         | Add reaction         |
| POST   | /api/messages/{id}/pin/              | Pin message          |
| GET    | /api/messages/{id}/thread/           | Get thread replies   |

### Search
| Method | Endpoint          | Description          |
|--------|-------------------|----------------------|
| GET    | /api/search/      | Search messages      |

### Files
| Method | Endpoint          | Description          |
|--------|-------------------|----------------------|
| POST   | /api/files/       | Upload file          |
| GET    | /api/files/{id}/  | Download file        |

## WebSocket Endpoints

| Endpoint                          | Description              |
|-----------------------------------|--------------------------|
| ws://host/ws/chat/{room_id}/      | Chat messages            |
| ws://host/ws/presence/            | Online presence          |
| ws://host/ws/notifications/       | User notifications       |

## Environment Variables

See `.env.example` for all available configuration options.

## Project Structure

```
chatnova/
├── backend/
│   ├── config/              # Django project settings
│   ├── apps/
│   │   ├── accounts/        # User management
│   │   ├── conversations/   # Conversations, channels, DMs
│   │   ├── messages_app/    # Messages, reactions, threads
│   │   ├── presence/        # Online status tracking
│   │   ├── notifications/   # Push notifications
│   │   ├── search/          # Message search
│   │   └── file_sharing/    # File uploads
│   ├── utils/               # Shared utilities
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/             # API client modules
│   │   ├── services/        # WebSocket, notifications
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── store/           # Redux store
│   │   ├── hooks/           # Custom React hooks
│   │   └── styles/          # Global CSS
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

## License

MIT License. See LICENSE file for details.
