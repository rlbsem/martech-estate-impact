"""Actual Chromium interactions, responsive layouts, accessibility and read-only boundaries."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from change_repository import ROOT, save, sha, source_hashes


def check(url, output):
    assert urlsplit(url).hostname in {"127.0.0.1", "localhost"}
    output = Path(output)
    if output.exists():
        raise ValueError("fresh browser output required")
    output.mkdir(parents=True)
    axe = ROOT / "change_tests/vendor/axe.min.js"
    assert (
        sha(axe.read_bytes()) == "880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb"
    )
    observations, scans, errors, external, writes, images = [], [], [], [], [], {}

    def require(name, value):
        assert value, name
        observations.append(dict(check=name, passed=True))

    def accessibility(page, state):
        result = page.evaluate(
            "async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return {violations:r.violations,incomplete:r.incomplete,passes:r.passes.length}}"
        )
        if result["violations"]:
            save(output / "accessibility-diagnostic.json", dict(state=state, **result))
        require("accessibility:" + state, not result["violations"])
        followups = []
        for issue in result["incomplete"]:
            for node in issue["nodes"]:
                target = page.locator(node["target"][0])
                require("unique accessibility target", target.count() == 1)
                target.scroll_into_view_if_needed()
                again = target.evaluate(
                    "async(e,id)=>{const r=await axe.run(e,{runOnly:{type:'rule',values:[id]}});return {violations:r.violations,incomplete:r.incomplete,passes:r.passes.length}}",
                    issue["id"],
                )
                if again["violations"] or again["incomplete"] or not again["passes"]:
                    save(
                        output / "accessibility-diagnostic.json",
                        dict(state=state, issue=issue, again=again),
                    )
                require(
                    "resolved incomplete:" + issue["id"],
                    not again["violations"] and not again["incomplete"] and again["passes"] > 0,
                )
                followups.append(dict(rule=issue["id"], target=node["target"], result=again))
        scans.append(dict(state=state, **result, followups=followups))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=dict(width=1440, height=1200), reduced_motion="reduce")
        page.add_init_script(script=axe.read_text(encoding="utf-8"))
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda r: external.append(r.url)
            if not r.url.startswith(url) and not r.url.startswith("blob:")
            else None,
        )
        page.on("request", lambda r: writes.append(r.method) if r.method != "GET" else None)
        page.goto(url)
        page.locator("#status").filter(has_text="Published snapshot").wait_for()
        recorded = page.request.get(url + "api/estate").json()
        require(
            "live persisted synthetic snapshot", recorded["synthetic"] and recorded["read_only"]
        )
        for width in [1440, 1024, 768, 390, 320]:
            page.set_viewport_size(dict(width=width, height=1000))
            for tab in ["estate", "changes", "evidence"]:
                button = page.locator(f'[data-tab="{tab}"]')
                button.focus()
                page.keyboard.press("Enter")
                require(
                    f"{width}:{tab}:keyboard navigation",
                    button.get_attribute("aria-pressed") == "true",
                )
                require(
                    f"{width}:{tab}:no page overflow",
                    not page.evaluate("document.documentElement.scrollWidth > innerWidth"),
                )
                require(f"{width}:{tab}:readable section", page.locator("#" + tab).is_visible())
                if width in [1440, 390]:
                    accessibility(page, f"{width}:{tab}")
        page.set_viewport_size(dict(width=1440, height=1200))
        page.locator('[data-tab="estate"]').click()
        previews = [v for v in recorded["versions"] if v["id"].startswith("explore:")]
        for v in previews:
            page.locator("#system").select_option(v["id"])
            numbers = page.locator("#impact-summary strong").all_text_contents()
            require(
                "persisted retirement:" + v["id"],
                int(numbers[0]) == len(v["assessment"]["failed_requirements"])
                and int(numbers[1]) == len(v["assessment"]["unknown_requirements"]),
            )
        page.locator("#system").select_option("explore:atlas/workbench")
        page.locator("#requirement").select_option("atlas/campaign")
        node = page.get_by_role("button", name="Inspect atlas/workbench", exact=True)
        node.focus()
        page.keyboard.press("Enter")
        require(
            "keyboard graph source inspection",
            "atlas/workbench" in page.locator("#node-detail").inner_text(),
        )
        require(
            "target unavailable node remains explicit", "UNSUPPORTED" in node.get_attribute("class")
        )
        page.locator("#requirements details summary").first.click()
        require(
            "witness visible",
            page.locator("#requirements details").first.locator("pre").is_visible(),
        )
        accessibility(page, "desktop:expanded witness and graph")
        page.locator('[data-tab="changes"]').click()
        for index, v in enumerate(recorded["versions"]):
            if v["id"].startswith("explore:"):
                continue
            page.locator("#proposal").select_option(str(index))
            require(
                "revision & state:" + v["id"] + str(v["revision"]),
                v["proposal"]["title"] in page.locator("#review").inner_text()
                and v["state"].replace("_", " ") in page.locator("#review").inner_text(),
            )
        page.locator('[data-tab="evidence"]').click()
        with page.expect_download() as event:
            page.locator("#download").click()
        downloaded = event.value.path().read_bytes()
        require("download equals exact API content", json.loads(downloaded) == recorded)
        require(
            "no database URL exported",
            b"postgresql://" not in downloaded and b"password=" not in downloaded,
        )
        for tab in ["estate", "changes", "evidence"]:
            for width in [1440, 390]:
                page.set_viewport_size(dict(width=width, height=1250 if width == 1440 else 1000))
                page.locator(f'[data-tab="{tab}"]').click()
                if tab == "changes":
                    chosen = next(
                        i
                        for i, v in enumerate(recorded["versions"])
                        if v["id"] == "replacement" and v["revision"] == 2
                    )
                    page.locator("#proposal").select_option(str(chosen))
                if tab == "estate":
                    page.locator("#requirements details").first.evaluate("e=>e.open=false")
                page.evaluate("scrollTo(0,0)")
                if width == 390:
                    page.locator("#" + tab + " .toolbar").first.evaluate(
                        "e=>e.scrollIntoView({block:'start'})"
                    )
                file = output / f"{tab}-{'desktop' if width == 1440 else 'mobile'}.png"
                page.screenshot(path=str(file))
                images[file.name] = dict(
                    sha256=sha(file.read_bytes()),
                    viewport=dict(width=width, height=1250 if width == 1440 else 1000),
                    tab=tab,
                )
        # This is a controlled UI outage only; database interruption tests are separate.
        page.route(
            "**/api/estate",
            lambda r: r.fulfill(status=503, json={"error": "controlled-browser-read-failure"}),
        )
        page.reload()
        page.locator("#status").filter(has_text="Evidence unavailable").wait_for()
        require(
            "unavailable data makes no readiness claim",
            page.locator("#metrics .metric").count() == 0,
        )
        accessibility(page, "mobile:unavailable evidence")
        for path in ["api/decide", "api/estate"]:
            response = page.request.post(url + path, data="{}")
            require("write endpoint rejected:" + path, response.status == 405)
        require(
            "path traversal rejected", page.request.get(url + "%2e%2e/schema.sql").status == 404
        )
        headers = page.request.get(url).headers
        require(
            "strict self CSP",
            "script-src 'self'" in headers["content-security-policy"]
            and "unsafe-inline" not in headers["content-security-policy"],
        )
        require("no application browser writes", not writes)
        require("no third-party browser requests", not external)
        require("no JavaScript errors", not errors)
        browser.close()
    result = dict(
        status="passed",
        captured_at=datetime.now(UTC).isoformat(),
        browser="Actual Playwright Chromium",
        source_sha256=source_hashes(),
        snapshot_id=recorded["snapshot"]["id"],
        checks=observations,
        accessibility=scans,
        screenshots=images,
        boundary="Real browser over local read-only PostgreSQL-backed synthetic console; no external deployment",
    )
    save(output / "browser.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.url, args.output)
    print(
        json.dumps(
            dict(checks=len(result["checks"]), accessibility_states=len(result["accessibility"]))
        )
    )
