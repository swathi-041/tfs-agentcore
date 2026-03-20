@echo off
python -c "import zipfile; import os; zipf = zipfile.ZipFile('%2', 'w', zipfile.ZIP_DEFLATED); [zipf.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), '%1')) for root, dirs, files in os.walk('%1') for f in files]; zipf.close()"
