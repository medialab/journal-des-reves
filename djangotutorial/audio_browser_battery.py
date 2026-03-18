import json
import os
import time
from typing import Any, Dict, List

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("AUDIO_TEST_BASE_URL", "http://127.0.0.1:8000")
LOGIN_URL = f"{BASE_URL}/accounts/login/?next=/polls/enregistrer/"
USERNAME = os.getenv("AUDIO_TEST_USERNAME", "audio_test_user")
PASSWORD = os.getenv("AUDIO_TEST_PASSWORD", "AudioTest123")


def evaluate_audio_state(page) -> Dict[str, Any]:
    return page.evaluate(
        """
        () => {
            const fileInput = document.getElementById('audioInput');
            const submitBtn = document.getElementById('submitBtn');
            const statusText = document.getElementById('statusText');
            const support = {
                mp4: typeof MediaRecorder !== 'undefined' ? MediaRecorder.isTypeSupported('audio/mp4') : false,
                webm: typeof MediaRecorder !== 'undefined' ? MediaRecorder.isTypeSupported('audio/webm;codecs=opus') : false,
                wav: typeof MediaRecorder !== 'undefined' ? MediaRecorder.isTypeSupported('audio/wav') : false,
                ogg: typeof MediaRecorder !== 'undefined' ? MediaRecorder.isTypeSupported('audio/ogg') : false,
            };

            const file = fileInput && fileInput.files && fileInput.files.length > 0 ? fileInput.files[0] : null;
            return {
                secureContext: window.isSecureContext,
                selectedFile: file ? {
                    name: file.name,
                    type: file.type,
                    size: file.size,
                } : null,
                submitEnabled: submitBtn ? !submitBtn.disabled : false,
                statusText: statusText ? statusText.textContent : null,
                mimeSupport: support,
            };
        }
        """
    )


def run_browser_test(playwright, browser_key: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "browser": browser_key,
        "ok": False,
        "errors": [],
        "console": [],
        "audio": None,
    }

    browser = None
    context = None

    try:
        if browser_key == "chromium":
            browser = playwright.chromium.launch(
                channel="chrome",
                headless=True,
                args=[
                    "--use-fake-device-for-media-stream",
                    "--use-fake-ui-for-media-stream",
                ],
            )
        elif browser_key == "firefox":
            browser = playwright.firefox.launch(
                headless=True,
                firefox_user_prefs={
                    "media.navigator.streams.fake": True,
                    "media.navigator.permission.disabled": True,
                },
            )
        else:
            raise RuntimeError(f"Unsupported browser key: {browser_key}")

        context = browser.new_context(ignore_https_errors=True)
        if browser_key == "chromium":
            context.grant_permissions(["microphone"], origin=BASE_URL)
        page = context.new_page()
        page.on("console", lambda msg: result["console"].append(msg.text))

        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            page.fill('input[name="username"]', USERNAME, timeout=5000)
            page.fill('input[name="password"]', PASSWORD, timeout=5000)
            page.click('button[type="submit"]', timeout=5000)
            page.wait_for_url("**/polls/enregistrer/**", timeout=15000)
        except Exception as auth_err:
            result["errors"].append(f"Auth error: {auth_err}. Attempting direct access...")
            page.goto(f"{BASE_URL}/polls/enregistrer/", wait_until="domcontentloaded", timeout=15000)

        page.wait_for_selector("#startBtn", timeout=15000)

        page.click("#startBtn")
        page.wait_for_selector("#stopBtn:not([disabled])", timeout=10000)
        time.sleep(1)
        page.click("#stopBtn")

        page.wait_for_selector("#audioPreview", state="visible", timeout=15000)
        state = evaluate_audio_state(page)
        result["audio"] = state

        if not state.get("selectedFile"):
            raise RuntimeError(f"No recorded audio file attached to #audioInput. State: {state}")

        if not state.get("submitEnabled"):
            raise RuntimeError(f"Submit button remained disabled. State: {state}")

        page.click("#submitBtn")
        page.wait_for_selector("#successMessageWithAudio", state="visible", timeout=25000)

        result["ok"] = True
        return result

    except (PlaywrightTimeoutError, PlaywrightError, RuntimeError) as exc:
        result["errors"].append(str(exc))
        return result

    finally:
        if context:
            context.close()
        if browser:
            browser.close()


def main() -> None:
    summary: List[Dict[str, Any]] = []

    with sync_playwright() as playwright:
        for browser in ["chromium", "firefox"]:
            summary.append(run_browser_test(playwright, browser))

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
