import modal

app = modal.App("test-decord")
img = modal.Image.debian_slim(python_version="3.11").pip_install("decord")

@app.function(image=img)
def test_import():
    import sys
    print("Python executable:", sys.executable)
    print("sys.path:", sys.path)
    try:
        import decord
        print("SUCCESS: decord imported successfully! Version:", getattr(decord, '__version__', 'unknown'))
    except Exception as e:
        import traceback
        print("FAILED to import decord:", traceback.format_exc())

@app.local_entrypoint()
def main():
    test_import.remote()
