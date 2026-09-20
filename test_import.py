import sys
try:
    import app
    print("app imported successfully")
except Exception as e:
    print("Error importing app:")
    import traceback
    traceback.print_exc()
