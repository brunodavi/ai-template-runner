```toml
extends = '../../conventional-commits.md'

[test]
type = 'feat'
```

Git status:
 M src/server.py
?? mserve.py

Staged diff:

Unstaged diff:
diff --git a/src/server.py b/src/server.py
--- a/src/server.py
+++ b/src/server.py
@@ -20,6 +20,15 @@ class Handler(BaseHTTPRequestHandler):
     def GET_root(self):
         return "OK"
 
+    def GET_health(self):
+        import time
+        return f"UP since {{time.ctime()}}"
+
 def serve(port):
     start(port)
