"""Helpers to fetch song metadata from online services with offline fallbacks."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Optional

import requests

ITUNES_SEARCH_ENDPOINT = "https://itunes.apple.com/search"
LYRICS_ENDPOINT_TEMPLATE = "https://api.lyrics.ovh/v1/{artist}/{title}"
REQUEST_TIMEOUT = 5  # seconds


def _build_data_url(binary: bytes, content_type: str | None) -> str:
    """Encode binary payload as a data URL usable by both Qt and HTML layouts."""
    if not binary:
        return ""
    mime = content_type or "application/octet-stream"
    encoded = base64.b64encode(binary).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _best_artwork_url(entry: dict) -> Optional[str]:
    """
    Try to pick the highest-resolution artwork URL from an iTunes API result.
    Apple uses a predictable pattern so we can upscale safely.
    """
    artwork = entry.get("artworkUrl100") or entry.get("artworkUrl60")
    if not artwork:
        return None
    # Promote artwork to 512px if the pattern matches "<size>x<size>"
    return artwork.replace("100x100bb", "512x512bb").replace("60x60bb", "512x512bb")


def get_album_art_data_url(title: str | None, artist: str | None) -> str:
    """
    Look up album artwork using the iTunes Search API and return it as a data URL.
    Returns an empty string when the network is unavailable or no art is found.
    """
    if not title and not artist:
        return ""

    query = " ".join(part for part in (artist, title) if part).strip()
    if not query:
        return ""

    params = {"term": query, "entity": "song", "limit": 1}
    try:
        response = requests.get(
            ITUNES_SEARCH_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"NETWORK ERROR fetching album art metadata: {exc}")
        return ""

    try:
        results = response.json().get("results") or []
    except ValueError as exc:
        print(f"ERROR parsing album art metadata response: {exc}")
        return ""
    if not results:
        return ""

    artwork_url = _best_artwork_url(results[0])
    if not artwork_url:
        return ""

    try:
        art_response = requests.get(artwork_url, timeout=REQUEST_TIMEOUT)
        art_response.raise_for_status()
    except requests.RequestException as exc:
        print(f"NETWORK ERROR downloading album art: {exc}")
        return ""

    content_type = art_response.headers.get("Content-Type")
    if not content_type:
        guessed_type, _ = mimetypes.guess_type(artwork_url)
        content_type = guessed_type or "image/jpeg"

    return _build_data_url(art_response.content, content_type)


def get_lyrics(title: str | None, artist: str | None) -> str:
    """Fetch lyrics from lyrics.ovh, returning descriptive fallbacks on failure."""
    if not title or not artist:
        return "Lyrics not available."

    url = LYRICS_ENDPOINT_TEMPLATE.format(artist=artist, title=title)

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"NETWORK ERROR fetching lyrics: {exc}")
        return "Lyrics not available (network error)."

    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            data = response.json()
        except ValueError as exc:
            print(f"ERROR parsing lyrics response: {exc}")
            data = {}
    else:
        data = {}
    lyrics = (data or {}).get("lyrics")
    if not lyrics:
        return "Lyrics not found."
    return lyrics.replace("\r\n", "\n").strip()


def load_local_placeholder_data_url(relative_path: str) -> str:
    """
    Utility to turn a bundled asset into a data URL so we can keep a single source
    of truth for the fallback artwork between Qt and HTML front-ends.
    """
    asset_path = Path(__file__).resolve().parents[1] / relative_path
    if not asset_path.exists():
        return ""
    content = asset_path.read_bytes()
    mime = mimetypes.guess_type(asset_path.name)[0] or "image/png"
    return _build_data_url(content, mime)
