## Requirements to run the project

- [Python 3.10+](https://www.python.org/downloads/)
- [MySQL Server 8.x](https://dev.mysql.com/downloads/mysql/) (MySQL Workbench recommended)
- Windows, macOS, or Linux


## 2. Python virtual environment

Open a terminal in the /project/ folder (the folder that contains `main.py` and `requirements.txt`).

### Windows (PowerShell) to set up .venv and install requirements.

```powershell
cd Project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### To run the program

```bash
python main.py
```

### Demo logins (GUI)

Shown on the login screen:

| Role | Username | Password |
| Teacher | `Tony_Stark` | `tstark123` |
| Student | `Harry_Potter` | `hpotter123` |

`(They also show on the login screen when you start the program)`