import os

# 测试环境统一禁用真实外部大模型与语音服务调用，
# 保证用例可离线、快速、可重复运行。
os.environ["DISABLE_EXTERNAL_AI"] = "1"
