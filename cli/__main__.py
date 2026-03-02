"""
🚀 智能视频制作系统 - CLI 参数入口
核心参数说明请参考 core/config.py 顶部的注释。
"""

# ====================================================================
#                           程序启动入口
# ====================================================================
if __name__ == "__main__":
    print("🚀 智能视频制作系统启动 (CLI)")
    
    # 设置项目路径
    import os
    import sys
    import shutil
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    def ensure_env_file(project_root: str) -> None:
        env_path = os.path.join(project_root, ".env")
        example_path = os.path.join(project_root, ".env.example")
        if os.path.exists(env_path):
            return
        if not os.path.exists(example_path):
            return
        try:
            shutil.copyfile(example_path, env_path)
            print("✅ 已生成 .env 文件，请补充必要密钥")
        except Exception as e:
            print(f"⚠️ .env 文件生成失败: {e}")

    try:
        ensure_env_file(project_root)
        from core.config import get_generation_params
        from cli.ui_helpers import run_cli_main, setup_cli_logging

        # 初始化 CLI 日志，使后续模块共享统一配置
        setup_cli_logging()

        default_params = get_generation_params()
        result = run_cli_main(**default_params)
        
        # 处理结果
        if result.get("success"):
            if result.get("final_video"):
                print("\n🎉 视频制作完成！")
            else:
                step_msg = result.get("message") or "已完成当前步骤"
                print(f"\n✅ {step_msg}")
        else:
            msg = result.get('message', '未知错误')
            if isinstance(msg, str) and ("用户取消" in msg or "返回上一级" in msg):
                print("\n👋 已返回上一级")
            elif result.get('needs_prior_steps') or (isinstance(msg, str) and "需要先完成前置步骤" in msg):
                print(f"\nℹ️ {msg}")
            else:
                print(f"\n❌ 处理失败: {msg}")
                
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        print("请确保在项目根目录下运行此脚本")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
