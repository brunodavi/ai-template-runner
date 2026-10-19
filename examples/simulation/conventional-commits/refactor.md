```toml
extends = '../../conventional-commits.md'

[test]
type = 'refactor'
```

Git status:
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	renamed:    examples/template-hello.md -> examples/features/hello.md
	renamed:    examples/simple/prompt.md -> examples/features/simple.md

Staged diff:
diff --git a/examples/template-hello.md b/examples/features/hello.md
similarity index 100%
rename from examples/template-hello.md
rename to examples/features/hello.md
diff --git a/examples/simple/prompt.md b/examples/features/simple.md
similarity index 98%
rename from examples/simple/prompt.md
rename to examples/features/simple.md
--- a/examples/simple/prompt.md
+++ b/examples/features/simple.md
@@ -1,5 +1,5 @@
 ```toml
 [provider]
-base_url = 'http://localhost:8080/v1/chat/completions'
+extends = '../base.md'
 model = 'lfm230m'
 ```

Unstaged diff:
