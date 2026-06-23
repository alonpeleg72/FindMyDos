from flask import Flask
import os

# Simulate what happens in findmydos/web/app.py
app = Flask(__name__)

print(f"__name__: {__name__}")
print(f"Template folder: {app.template_folder}")
print(f"Absolute template folder: {os.path.abspath(app.template_folder)}")
print(f"Template folder exists: {os.path.exists(app.template_folder)}")

# Check what the actual path should be based on where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
expected_template_dir = os.path.join(script_dir, 'templates')
print(f"\nScript directory: {script_dir}")
print(f"Expected template dir: {expected_template_dir}")
print(f"Expected template dir exists: {os.path.exists(expected_template_dir)}")

# Check if index.html exists in the expected location
index_path = os.path.join(expected_template_dir, 'index.html')
print(f"Index.html path: {index_path}")
print(f"Index.html exists: {os.path.exists(index_path)}")
