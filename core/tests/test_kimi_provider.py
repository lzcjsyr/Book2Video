def test_auto_detects_native_kimi_model_as_kimi():
    from core.startup import auto_detect_server_from_model

    assert auto_detect_server_from_model("kimi-k2.6", "llm") == "kimi"
