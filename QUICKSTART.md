# ⚡ Quick Start Guide (5 minutes)

**Want to get started immediately? Follow these steps.**

---

## Step 1: Prepare Environment (2 minutes)

```bash
# Navigate to project directory
cd c:\Users\AymenJallouli\Desktop\flask

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Database (2 minutes)

```bash
# Copy environment file
copy .env.example .env
```

**Edit `.env` and update MySQL credentials:**
```
DEV_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/network_slicing
```

**Create database (in MySQL console):**
```sql
CREATE DATABASE network_slicing;
USE network_slicing;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('system_admin', 'network_engineer', 'data_scientist', 'noc_operator') 
        DEFAULT 'network_engineer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);
```

## Step 3: Create Admin User (1 minute)

```bash
# Python interactive shell
python

# Then paste:
from app import create_app, db
from app.models.user import User

app = create_app('development')
with app.app_context():
    admin = User(username='admin', role='system_admin')
    admin.set_password('Admin@123456')
    db.session.add(admin)
    db.session.commit()
    print("✓ Admin user created!")
    
# Exit: type 'exit()'
```

## Step 4: Run Application (Press Enter)

```bash
python run.py
```

**You should see:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## Step 5: Login & Explore

1. **Open browser:** http://127.0.0.1:5000
2. **You'll be redirected to login:** http://127.0.0.1:5000/auth/login
3. **Login with:**
   - Username: `admin`
   - Password: `Admin@123456`
4. **You're in!** 🎉

---

## 📱 What You Can Do Now

### As Admin
- Access dashboard at `/`
- Manage users at `/admin/users/web`
- Create new users
- Change user roles
- Deactivate users

### Features to Try
- **Dashboard:** View metric cards
- **Profile:** Click username → Profil → Change password
- **Users:** Admin menu → Utilisateurs → Create/edit users
- **Logout:** Click username → Déconnexion

---

## 🔍 Next Steps

### Test the APIs
```bash
# Health check (no auth needed)
curl http://127.0.0.1:5000/admin/health

# Get users (auth required)
# See TEST_API.md for detailed examples
```

### Create More Users
1. Go to Admin → Utilisateurs
2. Click "Ajouter un utilisateur"
3. Fill form with:
   - Username: `engineer1`
   - Password: `EngineerPass123456`
   - Role: Network Engineer
4. Click "Créer l'utilisateur"

### Explore Code
- **Models:** `app/models/user.py`
- **Routes:** `app/blueprints/auth.py`, `admin.py`
- **Templates:** `app/templates/`
- **Config:** `config.py`

---

## 📚 Full Documentation

| Document | Time | Purpose |
|----------|------|---------|
| **README.md** | 10 min | Setup, install, deploy |
| **STRUCTURE.md** | 15 min | Architecture, models, design |
| **TEST_API.md** | 10 min | API examples, testing |
| **IMPLEMENTATION_SUMMARY.md** | 5 min | What was built, features |
| **VERIFICATION.md** | 10 min | Testing checklist |

---

## 🆘 Troubleshooting

### "MySQL connection failed"
```bash
# Check MySQL is running
mysql -u root -p -e "SELECT 1"

# Update .env with correct credentials
# DEV_DATABASE_URL=mysql+pymysql://root:your_password@...
```

### "Port 5000 already in use"
```bash
# Use different port
python run.py --port 5001
# Then access: http://127.0.0.1:5001
```

### "ModuleNotFoundError"
```bash
# Ensure venv is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "403 Forbidden" on admin page
- Make sure you're logged in as `admin`
- Other user roles cannot access admin pages

---

## ✅ Validation

Run this to verify everything is set up correctly:

```bash
python check_setup.py
```

Expected output:
```
✓ All checks passed! Project is ready to run.
```

---

## 🚀 You're Ready!

The application is fully functional and ready to use. 

**What's included:**
- ✅ User authentication (login/logout)
- ✅ Role-based access control (4 roles)
- ✅ Admin user management
- ✅ Modern dashboard
- ✅ Responsive design
- ✅ 6 MS-4 API endpoints
- ✅ Security best practices

**Next time you want to run the app:**
```bash
cd c:\Users\AymenJallouli\Desktop\flask
venv\Scripts\activate
python run.py
```

---

## 🎓 Common Tasks

### Add a New User (as admin)
1. Login as admin
2. Admin → Utilisateurs
3. Click "Ajouter un utilisateur"
4. Fill form and submit

### Change User Role
1. Admin → Utilisateurs
2. Click edit icon (pencil)
3. Select new role
4. Click "Enregistrer les modifications"

### Deactivate User
1. Admin → Utilisateurs
2. Click delete icon (ban/trash)
3. User will be marked inactive
4. They cannot login anymore

### Change Your Password
1. Click your username (top right)
2. Select "Profil"
3. Fill password change form
4. Click "Changer le mot de passe"

### Test API
```bash
# Create a new user via API
curl -X POST http://127.0.0.1:5000/admin/users \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session" \
  -d '{
    "username": "new_user",
    "password": "NewPass123456",
    "role": "network_engineer"
  }'
```

---

## 📞 Need Help?

1. Check **README.md** for detailed setup
2. Check **VERIFICATION.md** for testing steps
3. Check **TEST_API.md** for API examples
4. Check **STRUCTURE.md** for architecture details

---

**You're all set! Enjoy your Network Slicing Dashboard! 🎉**

If you have questions, refer to the documentation files or check the code comments.

---

**Quick Links:**
- Run app: `python run.py`
- Access: http://127.0.0.1:5000
- Admin panel: http://127.0.0.1:5000/admin/users/web
- Profile: http://127.0.0.1:5000/auth/profile
- Documentation: See README.md, STRUCTURE.md, TEST_API.md

**Total setup time: ~5-10 minutes**
