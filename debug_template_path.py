from flask import Flask
import os

app = Flask(__name__)

print(f"Current working directory: {os.getcwd()}")
print(f"Template folder: {app.template_folder}")
print(f"Template folder exists: {os.path.exists(app.template_folder)}")
if os.path.exists(app.template_folder):
    print(f"Files in template folder: {os.listdir(app.template_folder)}")
    if 'index.html' in os.listdir(app.template_folder):
        print("index.html found in template folder")
    else:
        print("index.html NOT found in template folder")
else:
    print("Template folder does not exist!")

# Also check relative to this script location
template_path = os.path.join(os.path.dirname(__file__), 'web', 'templates', 'index.html')
print(f"\nChecking relative path: {template_path}")
print(f"File exists: {os.path.exists(template_path)}")
