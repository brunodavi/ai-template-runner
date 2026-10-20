```toml
extends = '../../conventional-commits.md'

[out]
text = '{out.type}: {out.message}'

[test]
type = 'docs'
```

Git status:
 M README.md
Untracked files:
  docs/setup-guide.md

Staged diff:

Unstaged diff:
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -8,6 +8,12 @@
 ## Usage
 Install with pip:
 
+### Setup Guide
+
+1. Download the model weights from the release page.
+2. Extract them into the models directory.
+3. Set the MODEL_PATH environment variable.
+
 Run the server with:
 
 python -m server
