# 贡献指南

感谢你对 Glimmer 的兴趣！本文档介绍如何搭建开发环境、代码规范，以及如何为 Glimmer 添加新工具和新 LLM Provider。

项目概览、系统架构与完整文档索引见 [README.md](README.md)。

## 开发工作流

```bash
# 1. Fork 并克隆
git clone https://github.com/<你的用户名>/Glimmer.git
cd Glimmer

# 2. 安装依赖
pip install -r requirements.txt
cd web && npm install && cd ..

# 3. 创建特性分支
git checkout -b feature/my-feature

# 4. 修改前先跑测试
make test

# 5. 开发迭代
make dev              # 终端 1：后端
cd web && npm run dev # 终端 2：前端（Vite HMR）

# 6. 修改后跑测试
make test
cd web && npm test

# 7. 提交并推送
git commit -m "feat: 功能描述"
git push origin feature/my-feature
```

## 代码规范

- **Python**：必须包含类型标注。数据模型使用 Pydantic。全链路 async/await。
- **TypeScript**：严格模式。所有 Props 类型化。使用 CSS 变量而非硬编码颜色。
- **测试**：新功能需要测试。使用 `MockLLMAdapter` 避免网络依赖。
- **提交**：Conventional Commits（`feat:`、`fix:`、`docs:`、`test:`、`refactor:`、`chore:`）。

## 添加工具

1. 实现 `harness.tools.registry.Tool` 抽象基类
2. 在 `_build_default_tool_registry()` 中注册
3. 如需要，添加护栏规则（路径 + 白名单 + 正则）
4. 如工具产生可验证的结果，添加反馈分析策略
5. 使用 `MockLLMAdapter` 编写测试
6. 更新 [README 的工具参考](README.md#工具参考)

## 添加 LLM Provider

1. 实现 `harness.llm.adapter.LLMAdapter`
2. 在 `harness/llm/__init__.py` 中导出
3. 在 `_create_llm_from_config()` 中添加 Provider 检测逻辑
4. 更新前端 `SettingsPanel.tsx` Provider 下拉菜单
5. 更新 [README 的 LLM 供应商](README.md#llm-供应商)
