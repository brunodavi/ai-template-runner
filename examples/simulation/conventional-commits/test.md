```toml
extends = '../../conventional-commits.md'

[test]
type = 'test'
```

Git status:
 M test/test_cli.py

Staged diff:

Unstaged diff:
diff --git a/test/test_cli.py b/test/test_cli.py
--- a/test/test_cli.py
+++ b/test/test_cli.py
@@ -40,6 +40,16 @@ class TestCli(TestCase):
         self.assertIn('Hello', output_str)
         self.assertIn('TESTING', output_str)
 
+    def test_cli_run_with_empty_question(self):
+        output = StringIO()
+        with redirect_stdout(output):
+            cli(['run', get_template('template-hello'), ''])
+        self.assertIn('TESTING', output.getvalue())
+
 def test_cli_run_with_template_simple(self):
