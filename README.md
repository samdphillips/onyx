
## Install and Test

```
python3 -m venv _py36 &&
  source _py36/bin/activate && 
  pip install --upgrade pip && 
  pip install -r requirements.txt && 
  python setup.py install && 
  pytest tests
```