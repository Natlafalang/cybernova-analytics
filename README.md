# CyberNova Analytics — Web Platform
### CET333 Product Development | Natlafalang W.J.K Marapo

---

## Setup & Run Instructions

### Requirements
- Python 3.10+
- Flask (already in requirements.txt)

### Installation

1. **Unzip** the project folder
2. Open a terminal in the `cybernova/` directory
3. Install dependencies:
   ```
   pip install flask
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and go to:
   ```
   http://localhost:5000
   ```

---

## Admin Panel

- URL: `http://localhost:5000/admin/login`
- Username: `admin`
- Password: `admin123`

---

## AI Assistant — OpenAI Integration (Optional)

The AI assistant works out of the box with a smart rule-based fallback.
To enable live OpenAI responses:

1. Get a free API key from https://platform.openai.com
2. Set the environment variable before running:
   ```
   # Windows
   set OPENAI_API_KEY=your-key-here
   python app.py

   # Mac/Linux
   export OPENAI_API_KEY=your-key-here
   python app.py
   ```

---

## Project Structure

```
cybernova/
├── app.py                  Main Flask application (all routes + logic)
├── cybernova.db            SQLite database (auto-created on first run)
├── requirements.txt
├── README.md
├── static/
│   └── css/
│       └── style.css       Full CyberNova stylesheet
└── templates/
    ├── base.html           Public nav + footer layout
    ├── index.html          Homepage
    ├── contact.html        Contact Security Team form
    ├── testimonials.html   Testimonials + submission form
    ├── blog.html           Blog listing
    ├── blog_post.html      Single blog post
    ├── gallery.html        Photo gallery
    ├── chat.html           AI Assistant live chat
    └── admin/
        ├── base.html       Admin layout + sidebar
        ├── login.html      Password-protected login
        ├── dashboard.html  Stats + charts overview
        ├── requests.html   All requests with filters
        ├── breach_report.html  Incident frequency report
        ├── analytics.html  Full analytics dashboard
        ├── content.html    Blog/testimonial/gallery manager
        └── ai_report.html  AI incident report generator
```

---

## Features Implemented

### Public Client
- Homepage with services overview, case studies, testimonials preview
- Contact Security Team form (no account required)
- All submissions stored immediately with no priority filtering
- Blog articles on cybersecurity threats
- Photo gallery of training events
- AI Cyber Assistant live chat (24/7)
- Testimonial submission with star rating

### Admin Panel
- Password-protected login (bcrypt-equivalent SHA-256)
- Dashboard with live statistics and charts
- View and filter all security requests (by type, country, date)
- Breach report with monthly frequency charts
- Analytics dashboard (doughnut, bar, line charts)
- Content manager: publish blogs, approve/delete testimonials, add gallery items
- AI Incident Report Generator

### AI Assistant
- Live support mode for public clients
- Report generator mode for admin staff
- Works offline with smart rule-based fallback
- Optional OpenAI GPT-3.5 integration via environment variable
