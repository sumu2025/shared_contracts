"""
CI/CD环境的LogFire配置

此模块提供了针对CI/CD环境的LogFire配置和通用工具函数，
用于跟踪构建过程、测试结果和部署状..."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..monitor_interface import EventType, LogLevel, ServiceComponent
from ..monitor_models import MonitoringOptions
from .logfire_config import LogFireConfig


class CIMonitorConfig(LogFireConfig):
    """CI/CD环境的LogFire配置...."""

    def __init__(
        self,
        service_name: str,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        environment: str = "development",
        capture_errors: bool = True,
        debug: bool = False,
    ):
        """
        初始化CI监控配置

        Args:
            service_name: 服务名称
            api_key: LogFire API密钥（可选）
            project_id: LogFire项目ID（可选）
            environment: 环境名称（如'development', 'production'）
            capture_errors: 是否自动捕获错误
            debug: 是否开启调试模式
     ..."""
        # 从环境变量获取CI相关信息
        ci_env = self._detect_ci_environment()
        
        # 调用父类初始化
        super().__init__(
            service_name=service_name,
            api_key=api_key,
            project_id=project_id,
            environment=environment,
            capture_errors=capture_errors,
            debug=debug,
        )
        
        # 添加CI特定上下文信息
        self.default_context.update(ci_env)
    
    def _detect_ci_environment(self) -> Dict[str, Any]:
        """
        检测CI环境并返回相关信息
        
        Returns:
            包含CI环境信息的字典
     ..."""
        ci_info = {
            "ci_detected": False,
            "ci_provider": None,
            "ci_build_number": None,
            "ci_build_url": None,
            "ci_job_name": None,
            "ci_commit_sha": None,
            "ci_branch": None,
            "ci_repository": None,
        }
        
        # 检测GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            ci_info.update({
                "ci_detected": True,
                "ci_provider": "github_actions",
                "ci_build_number": os.environ.get("GITHUB_RUN_NUMBER"),
                "ci_build_url": f"https://github.com/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ.get('GITHUB_RUN_ID')}",  # noqa: E501
                "ci_job_name": os.environ.get("GITHUB_WORKFLOW"),
                "ci_commit_sha": os.environ.get("GITHUB_SHA"),
                "ci_branch": os.environ.get("GITHUB_REF"),
                "ci_repository": os.environ.get("GITHUB_REPOSITORY"),
            })
        
        # 检测GitLab CI
        elif os.environ.get("GITLAB_CI") == "true":
            ci_info.update({
                "ci_detected": True,
                "ci_provider": "gitlab_ci",
                "ci_build_number": os.environ.get("CI_PIPELINE_ID"),
                "ci_build_url": os.environ.get("CI_PIPELINE_URL"),
                "ci_job_name": os.environ.get("CI_JOB_NAME"),
                "ci_commit_sha": os.environ.get("CI_COMMIT_SHA"),
                "ci_branch": os.environ.get("CI_COMMIT_REF_NAME"),
                "ci_repository": os.environ.get("CI_PROJECT_PATH"),
            })
        
        # 检测Jenkins
        elif os.environ.get("JENKINS_URL"):
            ci_info.update({
                "ci_detected": True,
                "ci_provider": "jenkins",
                "ci_build_number": os.environ.get("BUILD_NUMBER"),
                "ci_build_url": os.environ.get("BUILD_URL"),
                "ci_job_name": os.environ.get("JOB_NAME"),
                "ci_commit_sha": os.environ.get("GIT_COMMIT"),
                "ci_branch": os.environ.get("GIT_BRANCH"),
                "ci_repository": os.environ.get("GIT_URL"),
            })
        
        return ci_info
    
    def log_build_start(self, component: ServiceComponent = ServiceComponent.CI) -> None:  # noqa: E501
        """
        记录构建开始事件
        
        Args:
            component: 服务组件
     ..."""
        self.client.info(
            message="Build started",
            component=component,
            event_type=EventType.BUILD_STARTED,
            context={
                "build_start_time": datetime.utcnow().isoformat(),
            },
        )
    
    def log_build_step(
        self, 
        step_name: str, 
        status: str, 
        duration_ms: Optional[float] = None, 
        details: Optional[Dict[str, Any]] = None,
        component: ServiceComponent = ServiceComponent.CI,
    ) -> None:
        """
        记录构建步骤事件
        
        Args:
            step_name: 步骤名称
            status: 步骤状态（'success', 'failure', 'skipped'等）
            duration_ms: 步骤持续时间（毫秒）
            details: 详细信息
            component: 服务组件
     ..."""
        context = {
            "step_name": step_name,
            "step_status": status,
        }
        
        if duration_ms is not None:
            context["duration_ms"] = duration_ms
        
        if details:
            context.update(details)
        
        log_level = LogLevel.INFO if status == "success" else LogLevel.ERROR
        
        self.client.log(
            level=log_level,
            message=f"Build step '{step_name}' {status}",
            component=component,
            event_type=EventType.BUILD_STEP,
            context=context,
        )
    
    def log_build_end(
        self, 
        status: str, 
        duration_ms: Optional[float] = None,
        artifacts: Optional[List[Dict[str, str]]] = None,
        component: ServiceComponent = ServiceComponent.CI,
    ) -> None:
        """
        记录构建结束事件
        
        Args:
            status: 构建状态（'success', 'failure'）
            duration_ms: 构建持续时间（毫秒）
            artifacts: 构建产物列表
            component: 服务组件
     ..."""
        context = {
            "build_status": status,
            "build_end_time": datetime.utcnow().isoformat(),
        }
        
        if duration_ms is not None:
            context["build_duration_ms"] = duration_ms
        
        if artifacts:
            context["artifacts"] = artifacts
        
        log_level = LogLevel.INFO if status == "success" else LogLevel.ERROR
        
        self.client.log(
            level=log_level,
            message=f"Build {status}",
            component=component,
            event_type=EventType.BUILD_COMPLETED,
            context=context,
        )
    
    def log_test_results(
        self,
        total: int,
        passed: int,
        failed: int,
        skipped: int = 0,
        duration_ms: Optional[float] = None,
        coverage: Optional[float] = None,
        component: ServiceComponent = ServiceComponent.CI,
    ) -> None:
        """
        记录测试结果
        
        Args:
            total: 测试总数
            passed: 通过的测试数
            failed: 失败的测试数
            skipped: 跳过的测试数
            duration_ms: 测试持续时间（毫秒）
            coverage: 测试覆盖率（百分比）
            component: 服务组件
     ..."""
        context = {
            "test_total": total,
            "test_passed": passed,
            "test_failed": failed,
            "test_skipped": skipped,
        }
        
        if duration_ms is not None:
            context["test_duration_ms"] = duration_ms
        
        if coverage is not None:
            context["test_coverage"] = coverage
        
        log_level = LogLevel.INFO if failed == 0 else LogLevel.ERROR
        
        self.client.log(
            level=log_level,
            message=f"Test results: {passed}/{total} passed, {failed} failed, {skipped} skipped",  # noqa: E501
            component=component,
            event_type=EventType.TEST_COMPLETED,
            context=context,
        )
    
    def log_deployment(
        self,
        environment: str,
        status: str,
        version: str,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        component: ServiceComponent = ServiceComponent.CI,
    ) -> None:
        """
        记录部署事件
        
        Args:
            environment: 部署环境
            status: 部署状态
            version: 部署版本
            duration_ms: 部署持续时间（毫秒）
            details: 详细信息
            component: 服务组件
     ..."""
        context = {
            "deploy_environment": environment,
            "deploy_status": status,
            "deploy_version": version,
            "deploy_time": datetime.utcnow().isoformat(),
        }
        
        if duration_ms is not None:
            context["deploy_duration_ms"] = duration_ms
        
        if details:
            context.update(details)
        
        log_level = LogLevel.INFO if status == "success" else LogLevel.ERROR
        
        self.client.log(
            level=log_level,
            message=f"Deployment to {environment} {status} for version {version}",
            component=component,
            event_type=EventType.DEPLOYMENT,
            context=context,
        )


def create_ci_monitor(options: MonitoringOptions) -> CIMonitorConfig:
    """
    创建CI监控配置
    
    Args:
        options: 监控选项
    
    Returns:
        CIMonitorConfig实例
 ..."""
    return CIMonitorConfig(
        service_name=options.service_name,
        api_key=options.api_key,
        project_id=options.project_id,
        environment=options.environment,
        capture_errors=options.capture_errors,
        debug=options.debug,
    )
