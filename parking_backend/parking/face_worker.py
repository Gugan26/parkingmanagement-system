import os
import sys
import json

# CRITICAL: Set this BEFORE other imports
os.environ["NUMPY_RELAX_UPPER_BOUND"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppress TF logs

try:
    from deepface import DeepFace
    import numpy as np
except ImportError as e:
    print(json.dumps({"error": f"Import error: {str(e)}"}))
    sys.exit(1)

def run_verification(temp_path, db_path):
    try:
        # Perform Face Verification
        dfs = DeepFace.find(img_path=temp_path, db_path=db_path, enforce_detection=False, silent=True)
        
        if len(dfs) > 0 and len(dfs[0]) > 0:
            matched_df = dfs[0]
            result_path = matched_df.iloc[0]['identity']
            print(json.dumps({"success": True, "identity": result_path}))
        else:
            print(json.dumps({"success": False, "error": "Face not recognized"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Missing arguments"}))
        sys.exit(1)
        
    temp_path = sys.argv[1]
    db_path = sys.argv[2]
    run_verification(temp_path, db_path)
