你在仓库根目录工作。

任务：处理 `{input_file}`，生成第一步 raw JSON 并保存到 `{output_json}`。

运行上下文：

- 先读取 `{skill_path}`，并按它指向的 references 执行。
- 工作目录：`{text_dir}`。需要落盘的中间产物放在这里，具体文件名和流程以 `{skill_path}` 为准。

用户额外要求：{extra_requirements}

Subagent 调用要求：

- 如果当前会话存在可调用的 subagent，每完成一个阶段性产物后，先检查所有 subagent 的 description。
- 第一稿完成并达标后，调用标题、封面文案、金句候选相关 subagent。
- 第一稿和第二稿完后，调用审稿和修改建议相关 subagent，获取建议。
- subagent 只辅助判断和产出，最终整合与 `{output_json}` 写入仍由你负责。

外层硬约束：

- 不要绕过 `{skill_path}`；具体读取策略、中间产物、写作流程和 JSON 输出契约都以该路径内容为准。
- 保存的 `{output_json}` 必须能被 Python `json.loads` 解析。
- 若用户额外要求与 `{skill_path}` 的硬约束或 JSON 输出契约冲突，以 `{skill_path}` 和输出契约为准。
