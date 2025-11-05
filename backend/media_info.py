import requests


def get_album_art(title, artist):
    query = f"{artist} {title}".replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={query}&entity=song"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results")
        if results:
            return results[0].get("artworkUrl100")
    return None


import requests

def get_lyrics(title, artist):
    """Fetches lyrics from lyrics.ovh API, handles network errors."""
    if not title or not artist:
        return "Lyrics not available."

    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    
    try:
        # Aggiungi un timeout per non rimanere bloccato per sempre
        response = requests.get(url, timeout=5) 
        
        if response.status_code == 200:
            data = response.json()
            # Pulisci un po' il testo dei testi
            return data.get("lyrics", "Lyrics not found.").replace('\r\n', '\n').strip()
        else:
            return "Lyrics not found."
    
    except requests.exceptions.RequestException as e:
        # Questo cattura TUTTI gli errori di rete (ConnectionError, Timeout, ecc.)
        print(f"NETWORK ERROR fetching lyrics: {e}")
        return "Lyrics not available (network error)."