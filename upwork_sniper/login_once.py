"""Manual login helper to capture an authenticated storage state for Upwork."""

import asyncio
from pathlib import Path
from typing import Any, Dict

from playwright.async_api import async_playwright

from . import BASE_DIR, load_config


async def _wait_for_user_ack() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: input("\nĐăng nhập xong Upwork trên cửa sổ vừa mở rồi nhấn Enter..."))


async def capture_storage_state(config: Dict[str, Any]) -> None:
    browser_conf = config.get("browser", {})
    auth_conf = config.get("auth", {})

    cookies_path = Path(browser_conf.get("cookies_path", "upwork_sniper/cookies.json"))
    cookies_path = (BASE_DIR / cookies_path.name) if not cookies_path.is_absolute() else cookies_path
    cookies_path.parent.mkdir(parents=True, exist_ok=True)

    login_url = auth_conf.get("login_url", "https://www.upwork.com/ab/account-security/login")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=browser_conf.get("user_agent"))
        page = await context.new_page()
        await page.goto(login_url, wait_until="domcontentloaded")

        print(
            "\n>>> Login helper <<<\n"
            "1. Đăng nhập vào Upwork bằng trình duyệt vừa bật.\n"
            "2. Vượt captcha (nếu có) rồi nhấn Enter trong terminal này.\n"
            "3. Script sẽ lưu cookies vào storage_state để crawler dùng lại.\n"
        )

        await _wait_for_user_ack()

        await context.storage_state(path=str(cookies_path))
        print(f"✅ Đã lưu cookies vào: {cookies_path}")

        await browser.close()


def main():
    config = load_config()
    asyncio.run(capture_storage_state(config))


if __name__ == "__main__":
    main()


