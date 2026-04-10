import importlib, sys
candidates = ("tmm.api.http_app", "ticmymail.app")
app = None
for cand in candidates:
    try:
        m = importlib.import_module(cand)
        if hasattr(m, "create_app"):
            app = m.create_app()
            print(f"Loaded app from: {cand}")
            break
    except Exception as e:
        pass
if not app:
    sys.exit("Could not import app factory (expected tmm.api.http_app:create_app or ticmymail.app:create_app)")
for r in app.routes:
    print(f"{sorted(list(r.methods))}  {r.path}")