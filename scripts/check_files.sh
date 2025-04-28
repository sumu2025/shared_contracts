#!/bin/bash
# 检查特定文件的flake8问题

cd /Users/peacock/Projects/AgentForge/shared_contracts
flake8 integration_tests/test_agent_model_integration.py integration_tests/test_agent_tool_integration.py --max-line-length=88 --extend-ignore=E203
