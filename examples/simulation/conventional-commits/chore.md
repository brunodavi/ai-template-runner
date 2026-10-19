```toml
extends = '../../conventional-commits.md'

[test]
type = 'chore'
```

Git status:
 M .gitignore

Staged diff:

Unstaged diff:
diff --git a/.gitignore b/.gitignore
--- a/.gitignore
+++ b/.gitignore
@@ -1,4 +1,5 @@
 .venv/
+build/
+dist/
 *.png
 __pycache__/
