# Virtualizor Controller

Welcome to my project! This repository contains the source code for our project. Please follow the instructions below to set up your development environment.

## Getting Started
Prerequisites
Make sure you have the following installed:

Python 3.x
pip (Python package installer)
### Installation
Clone the repository:

1. git clone https://github.com/Crimson-Amir/Virtualizor-Controller
2. cd projectname
3. Install the required dependencies:

4. pip install -r requirements.txt

## Setting Up private.py
To keep sensitive information secure, we use a private.py file. Follow these steps to create and configure it:

In the root directory of the project, create a file named private.py

Add the following fields to private.py:

### private.py:
```
telegram_bot_token = "your telegram bot token"

telegram_bot_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

ADMIN_CHAT_ID = you'r telegram id
```

Ensure private.py is added to your .gitignore file to prevent it from being tracked by Git:

```
echo "private.py" >> .gitignore
```

## Running the Project

After setting up private.py, you can run the project using the following command:

```
python main.py
```

## Contributing
We welcome contributions! Please read our Contributing Guidelines for more details.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
