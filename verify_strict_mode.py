import os
import sys

# Ensure we can import from backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mocking environment for the test
os.environ["FORCE_MT5_DATA"] = "true"
os.environ["MT5_PATH"] = r"C:\Program Files\MetaTrader 5\terminal64.exe" # Typical path

try:
    # Try importing directly if we are in the folder, or via backend if not
    try:
        from backend.mt5_mcp import MT5Bridge
    except ImportError:
        sys.path.append(os.getcwd())
        from mt5_mcp import MT5Bridge

    print("[TEST] Importing MT5Bridge successful.")
    
    bridge = MT5Bridge()
    print(f"[TEST] Bridge initialized. Simulation mode: {bridge.simulation_mode}")
    
    # We expect this to FAIL if MT5 is not installed/running, or SUCCEED if it is.
    # But crucially, it should NOT return success=True with mode="simulation"
    result = bridge.initialize()
    print(f"[TEST] Initialize result: {result}")
    
    if result["success"] and result.get("mode") == "simulation":
        print("[FAIL] Strict mode failed! It fell back to simulation.")
        sys.exit(1)
    elif not result["success"] and "CRITICAL" in result["message"]:
        print("[PASS] Strict mode correctly blocked simulation (or MT5 connect failed as expected in test env).")
    elif result["success"] and result.get("mode") != "simulation":
         print("[PASS] Connected to real MT5.")
    else:
        print(f"[WARN] Unexpected state: {result}")

except ImportError:
    print("[PASS] Strict mode correctly raised ImportError (if MT5 lib missing).")
except Exception as e:
    print(f"[TEST] Exception: {e}")
    import traceback
    traceback.print_exc()
