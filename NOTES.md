# Notes

## 敏感信息保护方案

**场景**: 代码里有敏感信息（如 Webhook URL），不能提交到 GitHub。

### 方案：环境变量注入

```python
# config.py
import os

LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK") or ""
```

- `config.py` 里留空，放心提交到仓库
- 实际值通过环境变量传入，不会泄露

### 配置方式

写入 shell 配置文件，每次打开终端自动加载：

```bash
# zsh（macOS 默认）
echo 'export LARK_WEBHOOK="https://your-webhook-url"' >> ~/.zshrc

# bash
echo 'export LARK_WEBHOOK="https://your-webhook-url"' >> ~/.bash_profile
```

### 运行

```bash
# 方式一：新开终端直接运行（shell 配置自动生效）
python3 main.py

# 方式二：手动传（临时覆盖）
LARK_WEBHOOK="https://your-url" python3 main.py
```

### 注意事项

- `~/.zshrc` 只在 zsh 交互式 shell 加载
- 非交互式 shell（如脚本、某些工具）不自动加载，需先 `source ~/.zshrc`
- 写入后执行 `source ~/.zshrc` 让当前终端立即生效
