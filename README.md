# Instagram Clone 📸

A full-featured Instagram clone built with Django and React-like frontend.

## 🚀 Quick Start (1 minute!)

```bash
git clone <your-repo-url>
cd Instagram
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit: **http://127.0.0.1:8000** 🎉

**That's it!** OAuth auto-configures automatically! ✨

## 🔧 OAuth Configuration

### 🚀 Automatic Setup (Default)
- OAuth **auto-configures** when you start the server
- Uses test credentials if no `.env` file found
- Uses real credentials if `.env` file exists
- **No manual setup needed!**
### 🔑 For Real Google Login
1. Get credentials from [Google Cloud Console](https://console.cloud.google.com/)
2. Create `.env` file:
```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
