from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from silicon_professor.engine.rtl import test_picorv32
result=test_picorv32()
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['status']=='passed' else 2 if result['status']=='unavailable' else 1)
