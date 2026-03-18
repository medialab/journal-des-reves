#!/usr/bin/env python3

import json
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = os.getenv("SAFARI_TEST_BASE_URL", "http://127.0.0.1:8001")
NGROK_SKIP_WARNING = os.getenv("NGROK_SKIP_WARNING", "0") in {"1", "true", "yes", "on"}


def inspect_page(page, path: str):
    url = f"{BASE_URL}{path}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(800)

    data = page.evaluate(
        """
        () => {
            const html = document.documentElement;
            const navMenu = document.getElementById('navMenu');
            const hamburger = document.getElementById('hamburger');
            const hero = document.querySelector('.hero-section');
            const navbar = document.querySelector('.navbar');

            const menuRect = navMenu ? navMenu.getBoundingClientRect() : null;
            const heroRect = hero ? hero.getBoundingClientRect() : null;

            return {
                isSecureContext: window.isSecureContext,
                pageTitle: document.title,
                currentUrl: window.location.href,
                isNgrokWarningPage: document.body
                    ? document.body.innerText.includes('You are about to visit')
                    : false,
                appVh: getComputedStyle(html).getPropertyValue('--app-vh').trim(),
                innerHeight: window.innerHeight,
                docClientHeight: document.documentElement.clientHeight,
                navbarBackdrop: navbar ? getComputedStyle(navbar).backdropFilter : null,
                navbarWebkitBackdrop: navbar ? getComputedStyle(navbar).webkitBackdropFilter : null,
                hasHamburger: !!hamburger,
                hasNavMenu: !!navMenu,
                navMenuActive: !!(navMenu && navMenu.classList.contains('active')),
                navMenuRight: navMenu ? getComputedStyle(navMenu).right : null,
                navMenuHeight: navMenu ? getComputedStyle(navMenu).height : null,
                navMenuViewportFit: menuRect ? {
                    top: menuRect.top,
                    bottom: menuRect.bottom,
                    viewportHeight: window.innerHeight,
                    overflowsViewport: menuRect.bottom > window.innerHeight + 1,
                } : null,
                heroMinHeight: hero ? getComputedStyle(hero).minHeight : null,
                heroHeight: heroRect ? heroRect.height : null,
                bodyOverflowX: getComputedStyle(document.body).overflowX,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                hasHorizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            };
        }
        """
    )
    return data


def hide_debug_toolbar(page):
    page.evaluate(
        """
        () => {
            const toolbar = document.getElementById('djDebug');
            if (toolbar) {
                toolbar.style.display = 'none';
            }
        }
        """
    )


def run():
    report = {
        "base_url": BASE_URL,
        "ngrok_skip_warning_header": NGROK_SKIP_WARNING,
        "engines": {},
        "errors": [],
    }

    with sync_playwright() as p:
        engines = ["webkit", "chromium", "firefox"]
        for engine_name in engines:
            engine_report = {"pages": {}, "errors": []}
            browser = None
            context = None
            try:
                engine = getattr(p, engine_name)
                browser = engine.launch(headless=True)
                extra_headers = {}
                if NGROK_SKIP_WARNING:
                    extra_headers["ngrok-skip-browser-warning"] = "1"

                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    extra_http_headers=extra_headers,
                )
                page = context.new_page()

                # Home page baseline
                engine_report["pages"]["/"] = inspect_page(page, "/polls/")
                hide_debug_toolbar(page)

                # Open hamburger to check off-canvas menu bounds on mobile viewport
                page.click("#hamburger", timeout=5000)
                page.wait_for_timeout(400)
                engine_report["pages"]["/polls/ menu_open"] = inspect_page(page, "/polls/")

                # Login page baseline
                engine_report["pages"]["/accounts/login/"] = inspect_page(page, "/accounts/login/")

            except PlaywrightTimeoutError as exc:
                engine_report["errors"].append(f"Timeout: {exc}")
            except Exception as exc:
                engine_report["errors"].append(str(exc))
            finally:
                if context:
                    context.close()
                if browser:
                    browser.close()
            report["engines"][engine_name] = engine_report

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
