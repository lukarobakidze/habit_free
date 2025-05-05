# Habit Free App

A modern habit tracking application that helps users break bad habits and build good ones. Built with Flask backend and Kivy frontend.

## Features

- **User Authentication**
  - Secure registration and login system
  - Session management
  - Password hashing

- **Habit Tracking**
  - Add and remove habits
  - Track elapsed time since quitting
  - Predefined common habits with benefits information
  - Custom habit creation

- **Message System**
  - Schedule future messages
  - Message masking for privacy
  - Toggle message visibility
  - Automatic message delivery

- **User Interface**
  - Clean, modern design
  - Light/Dark theme support
  - Responsive layout
  - Intuitive navigation

## Quick Start: Run with Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed

### Steps
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd habit_free
   ```
2. **(Optional) Add a `.env` file:**
   If you want to use custom environment variables, create a `.env` file in the project root. Example:
   ```env
   FLASK_SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   ```
3. **Build and start the app:**
   ```bash
   docker compose up --build
   ```
4. **Open your browser and go to:**
   [http://localhost:5001](http://localhost:5001)
   - You should see: `Welcome to Habit Free API!`
5. **To stop the app:**
   Press `Ctrl+C` in the terminal or run:
   ```bash
   docker compose down
   ```

---

## Manual Python Setup (Advanced/Optional)

If you want to run the app without Docker:

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation
1. **Create and activate virtual environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
2. **Install dependencies**
```bash
pip install -r requirements.txt
```
3. **Environment Configuration**
Create a `.env` file in the project root with:
```env
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```
4. **Start the Backend Server**
```bash
python app.py
```
The backend will run on http://localhost:5001

---

## Project Structure

```
habit_free/
├── app.py              # Flask backend server
├── app_kivy.py         # Kivy frontend application
├── habitapp.kv         # Kivy UI layout definitions
├── requirements.txt    # Project dependencies
├── Dockerfile          # Docker build instructions
├── docker-compose.yml  # Docker Compose config
├── .dockerignore       # Docker ignore file
├── README.md           # Project documentation
└── [other project files]
```

## Environment Variables
- `FLASK_SECRET_KEY` (optional, for session security)
- `FLASK_ENV` (optional, e.g., `development`)

## Usage Guide

1. **Registration & Login**
   - Create a new account or login with existing credentials
   - Username: 3-15 characters (letters, numbers, underscore)
   - Password: Minimum 4 characters

2. **Managing Habits**
   - Add habits from predefined list or create custom ones
   - View elapsed time since quitting
   - Delete habits you no longer want to track
   - View benefits information for predefined habits

3. **Message System**
   - Schedule messages for future dates
   - Mask/unmask messages for privacy
   - Delete messages you no longer need
   - Messages are automatically delivered on scheduled dates

4. **Profile Management**
   - View your profile information
   - Logout when finished

## Development

### Running Tests
```bash
python -m pytest
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions and classes

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask team for the amazing web framework
- Kivy team for the cross-platform UI framework
- All contributors and users of the application 