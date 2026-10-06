1. Co aktualnie działa (Zaimplementowane funkcje)
Backend & Architektura (Python / Flask)
Serwer Webowy: Podstawowa struktura serwera Flask z trasami (routes) obsługującymi API oraz edytor.

Praca na sesjach / projektach: Tworzenie i zapis stanu roboczego wierszy dialogowych oraz osi czasu w plikach JSON.

Interfejs Osi Czasu (Timeline): Podstawowa obsluga warstw tekstu, dżwięku i wideo na froncie (JavaScript).

Generowanie Głosu & Lektor AI
Integracja z Edge TTS: Działające darmowe generowanie ścieżek audio dla tekstu.

Wybór Lektora ElevenLabs (API):

Integracja z endpointami ElevenLabs API (/v1/voices).

Możliwość pobierania listy głosów z konta użytkownika (z powiązanym kluczem ELEVENLABS_API_KEY).

Wybór określonego ID głosu (voice_id), modyfikacja podstawowych parametrów (stability, similarity boost).

Obróbka Wideo (FFmpeg Engine)
Nakładanie Tekstu / Napisów: Generowanie plików .ass / .srt i renderowanie ich na wideo w pionowym formacie (9:16).

Łączenie Ścieżek (Audio Muxing): Podstawowe miksowanie wygenerowanego lektora z tłem wideo i muzyką podkładową.

🔴 2. Co obecnie NIE działa / wymaga poprawki
Błędy Synchronizacji przy Renderowaniu FFmpeg:

Przy niestandardowych klatkach lub zmiennej długości nakładanych audio z ElevenLabs/EdgeTTS, FFmpeg potrafi wyrzucić błąd przesunięcia czasowego (desynchronizacja audio i wideo).

Brak Asynchronicznego Generowania Audio w ElevenLabs:

Generowanie głosu przy wywołaniu ElevenLabs zapytania odbywa się synchronicznie (bloki w request-response serwera). Zapytanie do API zawiesza interfejs www na czas odpowiedzi.

Brak Obsługi Błędów Klucza API (ElevenLabs):

W przypadku braku środków na koncie ElevenLabs lub niepoprawnego API_KEY backend zwraca błąd 500 zamiast czytelnego komunikatu w interfejsie.

Brak Dynamicznego Podglądu na Żywo (Real-Time Preview):

Oś czasu w JavaScript nie renderuje natychmiastowego podglądu klatki wideo po przesunięciu suwaka – podgląd wymaga ponownego przeładowania wyrenderowanego fragmentu.

🛠️ 3. Czego brakuje do produkcyjnej wersji (Roadmap / Todo)
Na podstawie założeń projektowych, do pełnej sprawności aplikacji brakuje następujących elementów:

Kolejkowanie Zadań (Background Jobs):

Wdrożenie Celery lub Redis Queue (RQ) do procesowania renderowania FFmpeg i generowania audio z ElevenLabs w tle (zamiast blokowania interfejsu Flaska).

Zaawansowany Edytor Stylu Napisów:

Podgląd i edycja kolorów, czcionek, tła napisów (animowany "Word-by-Word Highlight" znany z TikToka).

Obsługa Voice Cloning / Custome Voices (ElevenLabs):

Dodanie opcji przełączania się między modelami ElevenLabs (eleven_multilingual_v2 vs eleven_turbo_v2) bezpośrednio z panelu www.

Automatyczne Docięcie Tła (Gameplay Auto-Crop):

Automatyczne kadrowanie i zapętlanie wideo tła (np. rozgrywki z gier) pod wymiar 1080x1920 (9:16) o zadanej długości wygenerowanego audio.

System Zarządzania Zasobami (Media Library):

Zakładka do wgrywania własnych tła wideo, efektów dźwiękowych (SFX) oraz biblioteki muzycznej z możliwością ustawiania poziomu głośności w tle.
