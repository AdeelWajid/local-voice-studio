from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.diagnostics import diagnostics
print(json.dumps(diagnostics(),indent=2))
