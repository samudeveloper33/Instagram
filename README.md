### 1. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 4. Database Setup
```bash
python manage.py migrate
```

### 5. Create Test User
```bash
python manage.py shell -c "from django.contrib.auth.models import User; from accounts.models import Profile; user = User.objects.create_user('testuser', 'test@example.com', 'testpass123'); Profile.objects.get_or_create(user=user); print('Test user created')"
```

### 6. Run the Server
```bash
python manage.py runserver
```

## Usage

1. **Access the application:** `http://127.0.0.1:8000/`
2. **Login with test credentials:**
   - Username: `testuser`
   - Password: `testpass123`
3. **Or register a new account:** `http://127.0.0.1:8000/register/`
4. **Or use Google OAuth** (if configured)
