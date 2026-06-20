#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-15 17:04:18
- 最近修改：2026-06-15 17:04:18
- 文件用途：封装淘系登录浏览器自动化兜底中的 NC 滑块识别、轨迹生成和拖动验证能力。
- 业务范围：适用于 API_login/API_TaoXi_login 下的淘宝 Havana 登录页自动化降级和独立调试脚本。
- 依赖入口：DrissionPage 页面对象、ddddocr、标准库 random/time/logging。
- 验收方式：修改后执行 py_compile；真实滑块效果需在单店铺登录调试中验证。
- 注意事项：本文件只处理浏览器页面上的滑块，不读取账号密码、不保存 Cookie、不做数据库写入。
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any


CONTAINER_SELECTORS = [
    "#nc_1_wrapper",
    ".nc-container",
    "#nocaptcha",
    ".nc_wrapper",
    "#nc-container",
]

BUTTON_SELECTORS = [
    "#nc_1_n1t",
    ".btn_slide",
    ".nc-lang-cnt span",
    "#nc_1_wrapper .btn_slide",
    ".btn-slide",
]

SUCCESS_SELECTORS = [
    ".icon_success",
    ".nc-lang-cnt .icon-ok",
    ".nc_iconfont.btn_ok",
]


def make_slide_track(distance: int) -> list[tuple[int, int]]:
    """生成模拟人工拖动的相对位移轨迹。"""
    if distance <= 0:
        return []

    track: list[tuple[int, int]] = []
    current = 0
    mid = max(distance * 3 // 4, 1)

    while current < mid:
        step = random.randint(4, 10)
        delta = min(step, mid - current)
        current += delta
        track.append((delta, random.randint(-1, 1)))

    overshoot = distance + random.randint(4, 10)
    while current < overshoot:
        step = random.randint(2, 5)
        delta = min(step, overshoot - current)
        current += delta
        track.append((delta, random.randint(-1, 2)))

    while current > distance:
        step = random.randint(1, 3)
        delta = min(step, current - distance)
        current -= delta
        track.append((-delta, random.randint(-1, 1)))

    return track


def _is_displayed(element: Any) -> bool:
    try:
        return bool(element.states.is_displayed)
    except Exception:
        return True


def _find_visible(page: Any, selectors: list[str], timeout: int = 2) -> tuple[Any | None, str | None]:
    for selector in selectors:
        try:
            element = page.ele(f"css:{selector}", timeout=timeout)
            if element and _is_displayed(element):
                return element, selector
        except Exception:
            continue
    return None, None


def _has_success_state(page: Any) -> bool:
    for selector in SUCCESS_SELECTORS:
        try:
            element = page.ele(f"css:{selector}", timeout=1)
            if element and _is_displayed(element):
                return True
        except Exception:
            continue
    try:
        return "login" not in page.url
    except Exception:
        return False


def handle_nc_slider(
    page: Any,
    max_retry: int = 4,
    logger: logging.Logger | Any | None = None,
) -> bool:
    """
    检测并处理淘宝 NC 滑块。

    返回 True 表示无滑块或滑块已通过；返回 False 表示检测到滑块但多次拖动未通过。
    """
    log = logger or logging.getLogger("tb_login")
    container, container_selector = _find_visible(page, CONTAINER_SELECTORS, timeout=2)
    if not container:
        log.info("  未检测到 NC 滑块，跳过")
        return True

    log.info(f"  检测到 NC 滑块容器: {container_selector}")

    try:
        import ddddocr
    except ImportError:
        log.warning("  ddddocr 未安装，无法自动处理 NC 滑块")
        return False

    detector = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    retry_count = max(int(max_retry or 1), 1)

    for attempt in range(1, retry_count + 1):
        log.info(f"  滑块第 {attempt}/{retry_count} 次尝试")
        try:
            button, button_selector = _find_visible(page, BUTTON_SELECTORS, timeout=2)
            if not button:
                log.warning("  未找到滑块按钮")
                time.sleep(1)
                continue

            background_bytes = container.get_screenshot(as_bytes=True)
            button_bytes = button.get_screenshot(as_bytes=True)
            match_result = detector.slide_match(button_bytes, background_bytes, simple_target=True)
            distance = int(match_result["target"][0])
            log.info(f"  滑块按钮={button_selector}，缺口偏移={distance}px")

            page.actions.move_to(button)
            time.sleep(random.uniform(0.2, 0.4))
            page.actions.hold()
            time.sleep(random.uniform(0.05, 0.15))
            for delta_x, delta_y in make_slide_track(distance):
                page.actions.move(delta_x, delta_y)
                time.sleep(random.uniform(0.004, 0.018))
            time.sleep(random.uniform(0.1, 0.2))
            page.actions.release()
            time.sleep(1.5)

            if _has_success_state(page):
                log.info("  NC 滑块通过")
                return True

            error_element, _error_selector = _find_visible(page, [".errloading", ".nc-error"], timeout=1)
            if error_element:
                try:
                    error_text = error_element.text.strip()
                except Exception:
                    error_text = ""
                if error_text:
                    log.warning(f"  滑块验证失败提示: {error_text}")
        except Exception as exc:
            log.warning(f"  滑块处理异常: {type(exc).__name__}: {exc}")

        time.sleep(1.2)

    log.error("  NC 滑块多次处理失败")
    return False
