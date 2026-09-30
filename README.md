
# 🔗 Linkly — Smart URL Shortener

**Make your links shorter and smarter.**

Linkly is a web-based URL shortener built with Flask and SQLite that transforms long URLs into short, shareable links. It supports custom aliases, link expiration, QR code generation, and click analytics through a clean, responsive dashboard.

🌐 **Live Demo:** [URL ](https://url-shortener-7mue.onrender.com/)

📂 **GitHub Repository:** [URL_Shortener](https://github.com/shatakshisingh28/URL_Shortener)

---

## ✨ Features

- **URL Shortening:** Convert long URLs into short, easy-to-share links.
- **Custom Aliases:** Create personalized short links using your preferred alias.
- **Link Expiration:** Set links to expire after 1 hour, 1 day, 7 days, or 30 days, or keep them indefinitely.
- **QR Code Generation:** Automatically generate QR codes for shortened URLs.
- **Click Analytics:** Track total clicks and view click activity over time.
- **Link Management:** View recently created links, their original URLs, creation dates, expiration dates, and click counts.
- **Delete Links:** Remove unwanted short links from your collection.
- **Input Validation:** Validate URLs and prevent invalid or duplicate custom aliases.
- **Responsive UI:** Access the dashboard on desktop, tablet, and mobile devices.
- **Error Handling:** Display helpful pages for missing and expired links.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Flask | Web framework and routing |
| SQLite | Database for links and click history |
| HTML5 | Page structure |
| CSS3 | Responsive styling and dashboard UI |
| JavaScript | Clipboard interactions and notifications |
| qrcode | QR code generation |
| Pillow | Image processing for QR codes |
| Chart.js | Click analytics visualization |
| Gunicorn | Production WSGI server |
| Render | Web application hosting |

---

## 📸 Application Preview

The Linkly dashboard includes:

- A URL shortening form
- Custom alias and expiration options
- A generated short-link result with a copy button
- A QR code for sharing
- A table of saved links
- Link statistics and analytics

> Add screenshots of your homepage and analytics page here to showcase your project.

---

## 📁 Project Structure

```text
URL_Shortener/
│
├── app.py                 # Flask application and routes
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
│
├── templates/
│   ├── index.html         # Main dashboard
│   ├── analytics.html     # Link analytics page
│   ├── 404.html           # Not-found page
│   └── expired.html       # Expired-link page
│
├── static/
│   └── style.css          # Application styling
│
└── urls.db                # SQLite database (created at runtime)
```

---

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/shatakshisingh28/URL_Shortener.git
cd URL_Shortener
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If Gunicorn is not already listed in `requirements.txt`, add it before deploying to Render:

```text
gunicorn==23.0.0
```

### 4. Start the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🚀 Deployment on Render

Linkly can be deployed as a Python web service on Render.

1. Push the project to GitHub.
2. Open the [Render Dashboard](https://dashboard.render.com/).
3. Select **New + → Web Service**.
4. Connect your GitHub repository.
5. Configure the service with the following settings.

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

6. Click **Create Web Service** and wait for deployment.
7. Open the public URL provided by Render.

### Database persistence

The application uses SQLite. On Render, the local filesystem may be temporary, so saved links and click history can be lost when the service is replaced or redeployed.

For persistent production data, configure a suitable persistent disk or migrate the database to PostgreSQL.

---

## 🔗 How It Works

1. The user enters a long URL and optionally specifies a custom alias and expiration period.
2. Flask validates the URL and checks whether the alias is available.
3. The application generates a short code or uses the requested custom alias.
4. Link information is saved in the SQLite database.
5. Visiting the short URL redirects the user to the original destination.
6. Each successful redirect increments the click count and records a timestamp.
7. The analytics page displays click activity over time.
8. A QR code can be generated to make the shortened link easy to share.

---

## 🔒 Validation and Link Expiration

- Only URLs with valid `http://` or `https://` schemes are accepted.
- Custom aliases must contain 3–20 characters.
- Allowed alias characters are letters, numbers, hyphens, and underscores.
- Reserved route names and already-used aliases are rejected.
- Expired links no longer redirect to their original destinations.

---

## 🔮 Future Improvements

- [ ] Migrate SQLite to PostgreSQL for persistent hosted storage.
- [ ] Add user authentication and personal dashboards.
- [ ] Add password-protected short links.
- [ ] Add date-range filters and more analytics.
- [ ] Add link search and sorting.
- [ ] Add automated tests and continuous integration.
- [ ] Add rate limiting and abuse prevention.

---

## 👩‍💻 Author

**Shatakshi Singh**

- GitHub: [@shatakshisingh28](https://github.com/shatakshisingh28)
- LinkedIn: [Shatakshi Singh](https://www.linkedin.com/in/shatakshi-singh-256625219/)

---

## 📄 License

This project is available for learning and personal portfolio use. Add a `LICENSE` file if you wish to distribute it under a specific open-source license.

---

⭐ If you find this project useful, consider giving the repository a star!
