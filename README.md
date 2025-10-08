1. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Start the server**
   ```bash
   python manage.py runserver
   ```

6. **Open your browser**
   - Visit: `http://127.0.0.1:8000`
   - The app will auto-configure OAuth on first startup!

