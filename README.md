# **E-Commerce Project**

## **Installation**
### 1. Clone the repository
```
git clone https://github.com/ssammarshall/e-commerce_project.git
```
### 2. Create a virtual environment
```
python -m venv venv

# Mac:
source venv/bin/activate

# Windows:
# Command Prompt (CMD): venv\Scripts\activate.bat
# PowerShell: venv\Scripts\Activate.ps1
```
### 3. Install dependencies
```
pipenv install -r requirements.txt
```
### 4. Apply migrations
```
python manage.py migrate
```
### 5. (Optional) Create superuser
```
python manage.py createsuperuser
```
### 6. Run the server
```
python manage.py runserver
```
Open in browser
(http://127.0.0.1:8000/)
