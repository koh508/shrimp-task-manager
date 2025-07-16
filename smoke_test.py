#!/usr/bin/env python3
"""
부하 없는 주요 시스템 Smoke Test
"""
import asyncio
import sys
import traceback


def print_result(name, success, msg):
    if success:
        print(f"✅ {name}: {msg}")
    else:
        print(f"❌ {name}: {msg}")


async def test_stability_monitor():
    try:
        from stability_monitor_fixed import StabilityMonitor

        monitor = StabilityMonitor()
        health = await monitor.run_health_checks()
        report = monitor.generate_health_report(health)
        print_result("안정성 모니터", True, f"상태: {report['overall_status']}")
    except Exception as e:
        print_result("안정성 모니터", False, str(e))
        traceback.print_exc()


async def test_backup_system():
    try:
        from backup_system_fixed import BackupManager

        manager = BackupManager()
        path = manager.create_backup("smoke")
        backups = manager.list_backups()
        print_result(
            "백업 시스템",
            True,
            f"백업 {len(backups)}개, 최근: {backups[0]['filename'] if backups else '없음'}",
        )
    except Exception as e:
        print_result("백업 시스템", False, str(e))
        traceback.print_exc()


async def test_plugin_system():
    try:
        from plugin_system import PluginManager

        manager = PluginManager()
        await manager.initialize_all_plugins()
        info = manager.get_plugin_info()
        print_result("플러그인 시스템", True, f"플러그인 {len(info)}개")
    except Exception as e:
        print_result("플러그인 시스템", False, str(e))
        traceback.print_exc()


async def test_performance_optimizer():
    try:
        from performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer()

        @optimizer.cached(ttl=10)
        async def f(x):
            return x * 2

        await f(3)
        await f(3)
        report = optimizer.get_optimization_report()
        print_result("성능 최적화", True, f"캐시 히트율: {report['cache_stats']['hit_rate']:.1f}%")
    except Exception as e:
        print_result("성능 최적화", False, str(e))
        traceback.print_exc()


def test_dashboard_system():
    try:
        from dashboard_system import DashboardData

        data = DashboardData()
        data.refresh_all_data()
        summary = data.get_dashboard_summary()
        print_result("대시보드 시스템", True, f"상태: {summary['system_status']}")
    except Exception as e:
        print_result("대시보드 시스템", False, str(e))
        traceback.print_exc()


async def main():
    await test_stability_monitor()
    await test_backup_system()
    await test_plugin_system()
    await test_performance_optimizer()
    test_dashboard_system()


if __name__ == "__main__":
    asyncio.run(main())
