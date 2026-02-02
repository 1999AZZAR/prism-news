# PRISM 💎

A minimalist, glassmorphic tech news aggregator.

## Features

- **Multi-Source:** Fetches from Hacker News and Reddit (r/worldnews, r/science, etc.)
- **Glassmorphism UI:** Clean, modern, dark-mode aesthetic.
- **Infinite Scroll:** Just keep scrolling.
- **Fast:** Pure vanilla JS + Tailwind CSS (via CDN).
- **Dynamic Categories:** Users can select specific categories, like "tech", and fetch related articles dynamically.

## Project Structure

- **Frontend:**
  - `index.html`: Main entry point for the UI.
  - `app.js`: Handles dynamic content loading, category navigation, and API calls.
  - **UI/Design:** Utilizes Tailwind CSS with glassmorphism and pastel themes.

- **Backend:**
  - `server.py`: Manages the API, serves the frontend, and fetches articles from external sources.
  - **API Endpoint:** `/api/news?category=<category>` provides news items in JSON format.

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone https://example.com/micro-news.git
   cd micro-news
   ```
2. Install dependencies and activate the environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Start the backend server:
   ```bash
   python server.py
   ```
4. Open `index.html` in your browser to view the application.

### Deployment

For deployment, use Docker Compose:

1. Build and start containers:
   ```bash
   docker-compose up --build
   ```

2. Access the application at `http://localhost:8000`.

## Contribution

Contributions are welcome! Feel free to fork, improve, and submit a pull request.