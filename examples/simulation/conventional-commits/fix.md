```toml
extends = '../../conventional-commits.md'
```

Git status:
 M src/cli.py

Staged diff:

Unstaged diff:
diff --git a/src/cli.py b/src/cli.py
--- a/src/cli.py
+++ b/src/cli.py
@@ -12,8 +12,12 @@ def parse(argv):
     if argv[1] == "run":
         template = open(argv[2])
-        question = argv[3]
-        question = question.strip()
+        try:
+            question = argv[3].strip()
+        except IndexError:
+            question = None
         process(template, question)
