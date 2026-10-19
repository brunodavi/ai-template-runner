```toml
extends = '../../conventional-commits.md'

[test]
type = 'style'
```

Git status:
 M src/cli.py

Staged diff:

Unstaged diff:
diff --git a/src/cli.py b/src/cli.py
--- a/src/cli.py
+++ b/src/cli.py
@@ -12,7 +12,9 @@ def main():
     args = argparse.ArgumentParser()
 
     if args.verbosity:
-        show_debug_info(  args )
-        logging.basicConfig( level=logging.DEBUG )
+        show_debug_info(args)
+        logging.basicConfig(level=logging.DEBUG)
