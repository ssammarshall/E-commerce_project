# **E-Commerce Project**

## **Installation**
### 1. Clone the repository
```
git clone https://github.com/ssammarshall/e-commerce_project.git
```
### 2. CD into project directory
```
cd e-commerce_project
```
### 3. Create a virtual environment
```
python -m venv venv

# Mac:
source venv/bin/activate

# Windows:
# Command Prompt (CMD): venv\Scripts\activate.bat
# PowerShell: venv\Scripts\Activate.ps1
```
### 4. Install dependencies
```
pip install -r requirements_dev.txt
```
### 5. Apply migrations
```
python manage.py migrate
```
### 6. (Optional) Create superuser
```
python manage.py createsuperuser
```
### 7. Run the server
```
python manage.py runserver
```
Open in browser: http://127.0.0.1:8000/
