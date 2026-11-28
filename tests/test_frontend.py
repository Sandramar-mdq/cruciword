from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_root_serves_modular_layout(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert '<html lang="es" data-theme="crema">' in html
    assert "/static/manifest.json" in html
    assert "/static/css/tailwind.css" in html
    assert "/static/css/themes.css" in html
    assert "/static/js/storage.js" in html
    assert "/static/js/theme.js" in html
    assert "/static/js/board.js" in html
    assert "/static/js/app.js" in html
    assert "Papel Crema" in html
    assert "Edición Domingo" in html
    assert "Pizarra Nocturna" in html
    assert "Sin cronómetros. Sin presión. A tu ritmo." in html
    for path in (
        "/static/js/api.js",
        "/static/js/audio.js",
        "/static/js/board.js",
        "/static/js/keyboard.js",
    ):
        assert path in html


def test_manifest_metadata_and_icons(client: TestClient) -> None:
    response = client.get("/static/manifest.json")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["name"] == "Cruciword"
    assert manifest["short_name"] == "Cruciword"
    assert manifest["display"] == "standalone"
    assert manifest["orientation"] == "any"
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["theme_color"].startswith("#")

    icons = manifest["icons"]
    assert any(icon["purpose"] == "maskable" for icon in icons)
    for icon in icons:
        icon_response = client.get(icon["src"])
        assert icon_response.status_code == 200
        assert icon_response.content


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/static/css/tailwind.css", "var(--cw-bg)"),
        ("/static/css/themes.css", "Balsamiq Sans"),
        ("/static/js/storage.js", "cruciword:sync-queue"),
        ("/static/js/api.js", "flushQueue"),
        ("/static/js/theme-init.js", "cruciword:theme"),
        ("/static/js/theme.js", "data-theme-choice"),
        ("/static/js/audio.js", "SpeechSynthesisUtterance"),
        ("/static/js/board.js", "cruciword:boardchange"),
        ("/static/js/keyboard.js", "data-key-action"),
        ("/static/js/app.js", "serviceWorker"),
        ("/static/sw.js", "CACHE_NAME"),
        ("/static/icons/icon.svg", "<svg"),
    ],
)
def test_static_assets_are_served(
    client: TestClient, path: str, expected: str
) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert expected in response.text


@pytest.mark.parametrize(
    "filename",
    [
        "balsamiq-sans-400-latin.woff2",
        "balsamiq-sans-400-latin-ext.woff2",
        "balsamiq-sans-700-latin.woff2",
        "balsamiq-sans-700-latin-ext.woff2",
    ],
)
def test_local_fonts_are_served(client: TestClient, filename: str) -> None:
    response = client.get(f"/static/fonts/{filename}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("font/woff2")
    assert response.content.startswith(b"wOF2")
    assert (STATIC_DIR / "fonts" / filename).stat().st_size > 0


def test_missing_static_asset_returns_404(client: TestClient) -> None:
    assert client.get("/static/no-existe.css").status_code == 404


def test_themes_apply_60_30_10_and_comic_style(client: TestClient) -> None:
    css = client.get("/static/css/themes.css").text

    for theme in ("crema", "domingo", "pizarra"):
        assert f'[data-theme="{theme}"]' in css
    assert "--cw-bg:" in css
    assert "--cw-cell: #ffffff;" in css
    assert "--cw-cell-ink: #000000;" in css
    assert "--cw-success: #d1fae5;" in css
    assert "--cw-review: #fef3c7;" in css
    assert "border: 2px solid var(--cw-outline);" in css
    assert "box-shadow: 3px 3px 0 var(--cw-shadow);" in css
    assert "min-height: 48px;" in css


def test_service_worker_uses_cache_first_with_offline_shell(client: TestClient) -> None:
    script = client.get("/static/sw.js").text

    assert "cache.addAll(PRECACHE_URLS)" in script
    assert "caches.match(request)" in script
    assert 'url.pathname.indexOf("/api/") === 0' in script
    assert 'request.mode === "navigate"' in script
    assert 'caches.match(OFFLINE_URL)' in script


def test_layout_exposes_keyboard_clue_audio_and_auth_controls(
    client: TestClient,
) -> None:
    html = client.get("/").text

    assert html.count('data-key="') == 26
    assert "".join(re.findall(r'data-key="([A-Z])"', html)) == (
        "QWERTYUIOPASDFGHJKLZXCVBNM"
    )
    assert html.count('data-key-action="') == 3
    for action in ("backspace", "toggle-direction", "check"):
        assert 'data-key-action="' + action + '"' in html
    assert html.count('inputmode="none"') == 2
    for glyph in ("⌫", "⇄", "✓"):
        assert glyph in html
    assert html.count('data-cell-index="') == 7
    assert html.count('class="cw-cell cw-cell--blocked"') == 18
    assert "data-demo-board" in html
    assert "data-board-grid" in html
    assert "data-level-select" in html
    assert "data-clue-list" in html
    assert "data-check-status" in html
    assert "Escribe y pulsa ✓ cuando quieras ver tu avance." in html
    assert "data-score-status" in html
    assert "data-clue-text=" in html
    assert "data-clue-audio" in html
    assert "data-auth-form" in html
    assert 'id="cw-sync-status"' in html
    assert "data-save-progress" in html


def test_css_keyboard_is_touch_friendly_and_fluid(client: TestClient) -> None:
    css = client.get("/static/css/themes.css").text

    assert ".cw-keyboard {" in css
    assert "grid-template-columns: repeat(5, minmax(48px, 1fr));" in css
    assert "grid-template-columns: repeat(10, minmax(48px, 1fr));" in css
    assert "gap: 0.5rem;" in css
    assert "@media (min-width: 640px)" in css
    assert "@media (min-width: 1024px)" in css
    assert "min-height: 48px;" in css
    assert "min-width: 48px;" in css
    assert "touch-action: manipulation;" in css
    assert r".min-h-\[48px\]" in css
    assert r".min-w-\[48px\]" in css
    assert "[hidden]" in css


def test_storage_keeps_session_audio_and_sync_queue(client: TestClient) -> None:
    script = client.get("/static/js/storage.js").text

    assert "cruciword:session" in script
    assert "cruciword:clues-audio" in script
    assert "getQueue" in script
    assert "removeQueued" in script


def test_api_client_uses_only_current_backend_endpoints(client: TestClient) -> None:
    script = client.get("/static/js/api.js").text

    assert "/api/auth/register" in script
    assert "/api/auth/login" in script
    assert "/api/users/me" in script
    assert '"/api/puzzles/" + id + "/progress"' in script
    assert '"/api/puzzles/" + id + "/check"' in script
    assert "loadPuzzles: loadPuzzles" in script
    assert "power_mode_used: false" in script
    assert "navigator.onLine" in script
    assert "flushQueue" in script


def test_keyboard_supports_touch_and_physical_input(client: TestClient) -> None:
    script = client.get("/static/js/keyboard.js").text

    assert 'addEventListener("keydown"' in script
    assert "/^[A-Z]$/" in script
    assert "data-key-action" in script
    assert "input, textarea, select, form" in script
    assert "ArrowLeft" in script
    assert "ArrowRight" in script
    assert "toggle-direction" in script
    assert "checkNow" in script
    assert "Tab" in script
    assert "Spacebar" in script
    assert "data-board-grid" in script
    assert "getAnswers: getAnswers" in script
    assert "refresh: refresh" in script


def test_audio_uses_local_speech_synthesis_only(client: TestClient) -> None:
    script = client.get("/static/js/audio.js").text

    assert "SpeechSynthesisUtterance" in script
    assert 'lang = "en-US"' in script
    assert "data-clue-audio" in script
    assert "setAudio(true)" in script


def test_service_worker_precaches_new_frontend_modules(client: TestClient) -> None:
    script = client.get("/static/sw.js").text

    assert "cruciword-static-v6" in script
    for path in ("api.js", "audio.js", "grid-engine.js", "board.js", "navigation.js", "keyboard.js"):
        assert f"/static/js/{path}" in script


def test_no_external_runtime_sources(client: TestClient) -> None:
    assets = (
        "/",
        "/static/css/themes.css",
        "/static/js/storage.js",
        "/static/js/api.js",
        "/static/js/theme.js",
        "/static/js/audio.js",
        "/static/js/board.js",
        "/static/js/keyboard.js",
        "/static/js/app.js",
        "/static/sw.js",
        "/static/manifest.json",
    )

    for asset in assets:
        assert "https://" not in client.get(asset).text


def test_level_selector_and_dynamic_board_are_rendered(client: TestClient) -> None:
    html = client.get("/").text

    for level in ("A1", "A2", "B1", "B2", "C1"):
        assert f'value="{level}"' in html
    assert "--cw-grid-cols: 5" in html
    assert 'data-focus-clue="1_down"' in html
    assert 'data-focus-clue="2_across"' in html
    assert "Tu mejor marca" in html


def test_board_client_uses_check_and_letter_feedback(client: TestClient) -> None:
    script = client.get("/static/js/board.js").text

    assert "checkAnswers" in script
    assert "cw-cell--correct" in script
    assert "cw-cell--review" in script
    assert "cw-cell--attention" in script
    assert "clearFeedback" in script
    assert "cruciword:boardchange\", clearFeedback" in script
    assert "setTimeout" not in script
    assert "scheduleCheck" not in script
    assert "saveProgress" in script
    assert "getAnswers: getAnswers" in script
    assert "loadPuzzle" in script


def _token(source: str, name: str) -> str:
    match = re.search(
        r"--" + re.escape(name) + r":\s*(#[0-9a-fA-F]{6})\s*;",
        source,
    )
    assert match is not None
    return match.group(1).lower()


def _rgb(color: str) -> tuple[float, float, float]:
    return tuple(int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))


def _luminance(color: str) -> float:
    channels = []
    for value in _rgb(color):
        channels.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(first: str, second: str) -> float:
    light = max(_luminance(first), _luminance(second))
    dark = min(_luminance(first), _luminance(second))
    return (light + 0.05) / (dark + 0.05)


def test_check_feedback_tokens_meet_aaa_contrast(client: TestClient) -> None:
    css = client.get("/static/css/themes.css").text
    dark = css.split('[data-theme="pizarra"]', 1)[1].split("}", 1)[0]

    success = _token(css, "cw-success")
    success_ink = _token(css, "cw-success-contrast")
    light_success_ink = _token(css, "cw-success-text")
    review = _token(css, "cw-review")
    review_ink = _token(css, "cw-review-contrast")
    dark_success_ink = _token(dark, "cw-success-text")
    dark_card = _token(dark, "cw-card")

    assert success == "#d1fae5"
    assert success_ink == "#064e3b"
    assert review == "#fef3c7"
    assert review_ink == "#78350f"
    assert _contrast(success, success_ink) >= 7
    assert _contrast(review, review_ink) >= 7
    assert _contrast(light_success_ink, "#fffcf2") >= 7
    assert _contrast(dark_success_ink, dark_card) >= 7
    assert ".cw-cell--correct" in css
    assert ".cw-cell--review" in css
    assert ".cw-feedback--review" in css
    assert ".cw-cell--attention" in css
