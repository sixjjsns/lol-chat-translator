# Contributing Guide / 贡献指南

Thank you for your interest in contributing! / 感谢你愿意为这个项目做贡献。

## How to contribute / 如何贡献

1. Fork the repository / Fork 本仓库
2. Create a feature branch / 创建功能分支：`git checkout -b feat/your-feature`
3. Make your changes / 进行修改
4. Run tests and lint / 运行测试与检查：
   ```bash
   pip install -e ".[dev]"
   ruff check src tests main.py
   pytest
   ```
5. Commit and push / 提交并推送
6. Open a Pull Request / 发起 Pull Request

## Code style / 代码规范

- Follow [PEP 8](https://peps.python.org/pep-0008/) / 遵循 PEP 8
- Run `ruff check` before committing / 提交前运行 ruff
- Keep functions small and focused / 函数保持短小、职责单一
- Add tests for new features / 新功能需附带测试

## Reporting issues / 报告问题

Please include: / 请附上：
- Steps to reproduce / 复现步骤
- Expected vs actual behavior / 预期与实际行为
- Environment (Windows version, Python version) / 环境信息
- Logs (with secrets removed) / 日志（已移除敏感信息）
