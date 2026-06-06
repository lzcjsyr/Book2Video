你在仓库根目录工作。

任务：处理 `{input_file}`，生成第一步 raw JSON 并保存到 `{output_json}`。

运行上下文：

- 先读取 `{skill_path}`，并按它指向的 references 执行。
- 工作目录：`{text_dir}`。需要落盘的中间产物放在这里，具体文件名和流程以 `{skill_path}` 为准。
- 如果当前会话存在可调用的 subagent，在每个阶段性产物完成后，必须先检查 subagent 的 description；若某个 subagent 的 description 与当前阶段匹配，就用 Agent 工具调用对应的 subagent_type。不要用通用 Agent 代替已有专门 subagent。

用户额外要求：{extra_requirements}

外层硬约束：

- 不要绕过 `{skill_path}`；具体读取策略、中间产物、写作流程和 JSON 输出契约都以该路径内容为准。
- 保存的 `{output_json}` 必须能被 Python `json.loads` 解析。
- 若用户额外要求与 `{skill_path}` 的硬约束或 JSON 输出契约冲突，以 `{skill_path}` 和输出契约为准。
