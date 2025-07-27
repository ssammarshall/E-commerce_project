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

# Using Mac:
source venv/bin/activate

# OR using Windows:
# Command Prompt (CMD): venv\Scripts\activate.bat
# PowerShell: venv\Scripts\Activate.ps1
```
### 4. Run project in development or production
```
# DEVELOPMENT (includes debug-toolbar and pytest):

# Using Makefile:
make dev
# OR using Windows:
# Command Prompt (CMD): .\dev.bat
# PowerShell: .\dev.ps1


# PRODUCTION:

# Using Makefile:
make prod
# OR using Windows:
# Command Prompt (CMD): .\prod.bat
# PowerShell: .\prod.ps1

```
Open in browser: http://127.0.0.1:8000/
