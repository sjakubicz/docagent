# KnowledgeBase

Baza wiedzy projektu docagent: czym jest każda użyta technologia i gdzie dokładnie pracuje w aplikacji. Ścieżki są względem katalogu repozytorium.

## Spis treści

1. [Jak działa aplikacja (przepływy)](#1-jak-działa-aplikacja-przepływy)
2. [RAG i wyszukiwanie](#2-rag-i-wyszukiwanie)
3. [LLM i agent](#3-llm-i-agent)
4. [Backend](#4-backend)
5. [Baza danych](#5-baza-danych)
6. [Testy i jakość kodu](#6-testy-i-jakość-kodu)
7. [Frontend](#7-frontend)
8. [Infrastruktura i CI/CD](#8-infrastruktura-i-cicd)
9. [Licencje](#9-licencje)

---

## 1. Jak działa aplikacja (przepływy)

**Wgrywanie dokumentu**
1. Frontend wysyła PDF na `POST /api/documents` (`frontend/src/hooks/useDocuments.ts`).
2. Backend zapisuje oryginalny plik w `documents.content`, tworzy wiersz ze statusem `processing` i od razu odpowiada `202 Accepted` (`backend/src/docagent/api/routes.py`).
3. W tle (`BackgroundTasks`) uruchamia się `process_document` (`backend/src/docagent/ingest/pipeline.py`): ekstrakcja tekstu → OCR stron bez tekstu → chunking → embeddingi → zapis stron i chunków → status `ready` (albo `failed` z komunikatem błędu) → przebudowa indeksu BM25.
4. Frontend co 1,5 s odświeża listę, dopóki jakiś dokument ma status `processing`.

**Podgląd dokumentu**
1. Kliknięcie nazwy pliku w zakładce Documents otwiera szufladę (`DocumentPreview`).
2. `GET /api/documents/{id}` zwraca dokument ze stronami (tekst i flaga `ocr` dla każdej strony); zakładka „Extracted text” pokazuje dokładnie ten tekst, który przeszukuje agent.
3. Zakładka „Original” osadza `GET /api/documents/{id}/file` (oryginalny PDF z bazy) w `<iframe>`, więc przeglądarka wyświetla go swoim wbudowanym czytnikiem.

**Pytanie w czacie**
1. Frontend wysyła pytanie, historię rozmowy i ustawienia agenta (`options`: tryb wyszukiwania, liczba fragmentów na wyszukiwanie, limit kroków) na `POST /api/chat`. Domyślne ustawienia przychodzą z `GET /api/chat/options` (wartości z `.env`), a zmienione przez użytkownika są zapamiętywane w `localStorage`.
2. Graf LangGraph (`backend/src/docagent/agent/graph.py`): węzeł `retrieve` zawsze wykonuje wyszukiwanie dla pytania (w trybie z ustawień) → węzeł `agent` wywołuje LLM z dostępnymi narzędziami → jeśli model poprosi o narzędzie, węzeł `tools` je wykonuje i wraca do `agent` → koniec, gdy model odpowie bez wywołania narzędzia albo skończy się budżet kroków.
3. API zwraca odpowiedź, użyte ustawienia, czas działania i pełny ślad: każde wywołanie narzędzia z argumentami, zwróconymi fragmentami (z wynikiem trafności), tekstem wyniku i flagą błędu. W czacie ślad jest pod przyciskiem „Details” jako oś czasu kroków.

**Ewaluacja**
- `uv run python -m docagent.eval` (`backend/src/docagent/eval/__main__.py`) zadaje 20 pytań z `data/eval/questions.json` w trzech trybach wyszukiwania i liczy metryki.

---

## 2. RAG i wyszukiwanie

### RAG (Retrieval-Augmented Generation)
**Definicja:** wzorzec, w którym model językowy przed odpowiedzią dostaje fragmenty dokumentów wyszukane dla pytania. Odpowiedź opiera się na dostarczonym tekście, a nie tylko na wiedzy z treningu, dzięki czemu może dotyczyć prywatnych dokumentów i podawać źródła. Składa się z dwóch faz: **indeksowania** (podział dokumentów, embeddingi, zapis) i **zapytania** (wyszukiwanie, budowa kontekstu, generowanie).
**W docagent:** indeksowanie to `backend/src/docagent/ingest/`, wyszukiwanie to `backend/src/docagent/search/`, generowanie to agent w `backend/src/docagent/agent/`. Agent cytuje źródła jako `[plik, p. N]`.

### Ekstrakcja tekstu z PDF (pdfplumber)
**Definicja:** PDF może mieć warstwę tekstową (tekst zapisany jako znaki z pozycjami) albo być samym obrazem (skan). pdfplumber to biblioteka Pythona (MIT), która czyta warstwę tekstową strona po stronie i umie wyrenderować stronę do obrazu (przez pypdfium2).
**W docagent:** `backend/src/docagent/ingest/pdf.py`: `page.extract_text()` dla każdej strony; `page.to_image(resolution=300)` dla stron do OCR.

### OCR (Tesseract)
**Definicja:** Optical Character Recognition, czyli rozpoznawanie tekstu na obrazie. Tesseract to silnik OCR na licencji Apache 2.0, a `pytesseract` to wrapper wywołujący go z Pythona.
**W docagent:** `backend/src/docagent/ingest/pdf.py`: jeśli strona ma mniej niż 20 znaków tekstu (`MIN_TEXT_CHARS`), jest renderowana w 300 DPI i czytana przez `pytesseract.image_to_string`. Liczba stron po OCR jest zapisywana w `documents.ocr_pages` i pokazywana w UI. Przykład skanu: `data/samples/knee_surgery_instructions_scan.pdf`.

### Chunking
**Definicja:** dzielenie tekstu na mniejsze fragmenty (chunki), które osobno się indeksuje i wyszukuje. Za duże chunki rozmywają znaczenie embeddingu i zużywają kontekst LLM-a; za małe gubią kontekst. **Overlap** (zakładka) powtarza końcówkę poprzedniego chunka na początku następnego, żeby zdanie przecięte granicą nie zginęło.
**W docagent:** `backend/src/docagent/ingest/chunking.py`: okna ok. 800 znaków z zakładką 150 (`CHUNK_SIZE`, `CHUNK_OVERLAP` w `config.py`), cięte na granicach słów. Chunking działa w obrębie strony, więc każdy chunk ma numer strony do cytowania.

### Embeddingi
**Definicja:** wektor liczb reprezentujący znaczenie tekstu, wygenerowany przez model. Teksty o podobnym znaczeniu mają bliskie wektory, nawet jeśli używają innych słów. Niektóre modele wymagają **prefiksów zadań**, które rozróżniają zapytanie od dokumentu.
**W docagent:** model `nomic-embed-text` (768 wymiarów) przez Ollamę; `backend/src/docagent/llm.py` wysyła teksty partiami po 64 i dokleja prefiksy `search_document: ` (chunki) oraz `search_query: ` (pytania). Wektory są w kolumnie `chunks.embedding`.

### Wyszukiwanie wektorowe i podobieństwo cosinusowe
**Definicja:** wyszukiwanie najbliższych wektorów do wektora zapytania. **Podobieństwo cosinusowe** mierzy kąt między wektorami (1 = ten sam kierunek); **odległość cosinusowa** = 1 − podobieństwo.
**W docagent:** `vector_search` w `backend/src/docagent/search/hybrid.py`: `Chunk.embedding.cosine_distance(qvec)` sortowane rosnąco; zwracane podobieństwo to `1 − odległość`.

### BM25 (bm25s)

**Definicja w skrócie:** BM25 (Best Matching 25) to algorytm rankingowy wyszukiwania pełnotekstowego, czyli po słowach, a nie po znaczeniu. Dla zapytania liczy wynik każdego dokumentu jako sumę wkładów słów z zapytania, które w dokumencie występują. Wkład słowa rośnie, gdy słowo jest **rzadkie w całym zbiorze**, gdy **występuje w dokumencie częściej** (ale z nasyceniem) i gdy **dokument jest krótszy** od przeciętnego. To standard w wyszukiwarkach (Lucene, Elasticsearch, OpenSearch) i punkt odniesienia dla wyszukiwania wektorowego.

#### Skąd się wziął

BM25 wywodzi się z probabilistycznego modelu wyszukiwania (Robertson, Spärck Jones i in., lata 70.–90.). „BM” to Best Matching, a 25 to numer wariantu funkcji z serii eksperymentów w systemie Okapi. Rozwija prostsze **TF-IDF** (term frequency × inverse document frequency) o dwie poprawki: nasycenie częstości słowa i normalizację długości dokumentu.

#### Krok 0: tokenizacja

Zanim cokolwiek się policzy, tekst zamienia się na listę tokenów (słów). Od tego zależy, co w ogóle może się dopasować. W `bm25s.tokenize` z ustawieniami docagent:
1. **Zamiana na małe litery:** `Metformin` i `metformin` to ten sam token.
2. **Podział regexem `\b\w\w+\b`:** token to ciąg co najmniej **dwóch** znaków alfanumerycznych. Pojedyncze znaki odpadają.
3. **Usunięcie stopwords angielskich** (`the`, `of`, `for`, `is`…): słowa tak częste, że nic nie mówią o treści.
4. **Bez stemmingu:** `doses` i `dose` to różne tokeny.

Przykład: `"Fever above 38.5 C, take 1 g; doses vs dose"` → `['fever', 'above', '38', 'take', 'doses', 'vs', 'dose']`. Odpadły `5`, `c`, `1`, `g` (jeden znak), a `38.5` zamieniło się w `38`. Dlatego zapytanie „1 g” nic nie znajdzie przez BM25, a zapytanie o „dose” nie dopasuje „doses”. Te braki pokrywa wyszukiwanie wektorowe w hybrydzie.

#### Wzór

Dla zapytania Q złożonego z tokenów q₁…qₙ i dokumentu D:

```
score(D, Q) = Σ  IDF(qᵢ) · TF_part(qᵢ, D)
             qᵢ∈Q

TF_part(q, D) = tf(q, D) / ( tf(q, D) + k1 · (1 − b + b · |D| / avgdl) )

IDF(q) = ln( 1 + (N − df(q) + 0.5) / (df(q) + 0.5) )
```

Oznaczenia:
- `tf(q, D)`: ile razy token q występuje w dokumencie D (term frequency).
- `|D|`: długość dokumentu w tokenach (po tokenizacji).
- `avgdl`: średnia długość dokumentu w całym zbiorze.
- `N`: liczba dokumentów w zbiorze.
- `df(q)`: w ilu dokumentach występuje q (document frequency).
- `k1` i `b`: parametry; w bm25s domyślnie `k1 = 1.5`, `b = 0.75`.

Słowa z zapytania, których dokument nie zawiera, dokładają 0. Słowa z zapytania nieobecne w całym zbiorze nic nie wnoszą do żadnego dokumentu.

#### Co robi każdy składnik

**IDF: rzadkie słowa ważą więcej.** Słowo występujące w prawie każdym dokumencie (np. `daily` w ulotkach leków) słabo odróżnia dokumenty, a słowo występujące w jednym (np. `lisinopril`) jest bardzo informatywne. Dla N = 3:

| df (w ilu dokumentach) | IDF |
|---|---|
| 1 | ln(1 + 2.5/1.5) = **0.981** |
| 2 | ln(1 + 1.5/2.5) = 0.470 |
| 3 (we wszystkich) | ln(1 + 0.5/3.5) = **0.134** |

„+1” w logarytmie to wariant Lucene. Oryginalny wzór Robertsona `ln((N − df + 0.5)/(df + 0.5))` daje **ujemne** IDF dla słów obecnych w ponad połowie dokumentów, czyli takie słowo obniżałoby wynik. Wersja z +1 jest zawsze dodatnia.

**TF z nasyceniem: kolejne wystąpienia dają coraz mniej.** W prostym TF-IDF dokument z 10 wystąpieniami słowa dostaje 10 razy więcej punktów niż z jednym, co premiuje powtarzanie słów (spam słów kluczowych). W BM25 wkład dąży do górnej granicy. Dla dokumentu o średniej długości (`|D| = avgdl`, więc nawias = 1) i `k1 = 1.5`:

| tf | TF_part = tf / (tf + 1.5) |
|---|---|
| 0 | 0 |
| 1 | 0.40 |
| 2 | 0.57 |
| 3 | 0.67 |
| 10 | 0.87 |
| ∞ | 1.00 |

`k1` steruje tym nasyceniem: `k1 = 0` całkowicie ignoruje częstość (liczy się tylko obecność słowa), a duże `k1` zbliża zachowanie do zwykłego TF.

**Normalizacja długości: krótszy dokument z tym samym trafieniem wygrywa.** Długi dokument ma więcej słów, więc częściej przypadkiem zawiera słowo z zapytania. Czynnik `(1 − b + b · |D|/avgdl)` w mianowniku zwiększa się dla dokumentów dłuższych od średniej i zmniejsza dla krótszych. `b` mówi, jak mocno: `b = 0` wyłącza normalizację, `b = 1` stosuje ją w pełni, a `0.75` to kompromis z praktyki.

**Wariant Lucene a „klasyczny”.** Podręcznikowy wzór ma w liczniku `tf · (k1 + 1)`. Lucene i bm25s (`method="lucene"`) pomijają `(k1 + 1)`. To stała, która mnoży wszystkie wyniki tak samo, więc **kolejność dokumentów się nie zmienia**, zmienia się tylko skala liczb.

#### Przeliczony przykład (zgodny z bm25s co do szóstego miejsca po przecinku)

Zbiór (po tokenizacji):

| Dok. | Tekst | Tokeny | \|D\| |
|---|---|---|---|
| 0 | Metformin dose: 500 mg daily. | metformin, dose, 500, mg, daily | 5 |
| 1 | Lisinopril 10 mg daily for blood pressure. | lisinopril, 10, mg, daily, blood, pressure | 6 |
| 2 | Asthma inhaler, two puffs daily. | asthma, inhaler, two, puffs, daily | 5 |

`N = 3`, `avgdl = 16/3 ≈ 5.333`. Zapytanie: `daily lisinopril dose`.

IDF: `dose` i `lisinopril` mają df = 1 → **0.9808**; `daily` ma df = 3 → **0.1335**.

Czynnik długości `k1 · (1 − b + b·|D|/avgdl)`:
- dokumenty 0 i 2 (|D| = 5): `1.5 · (0.25 + 0.75 · 0.9375) = 1.4297`;
- dokument 1 (|D| = 6): `1.5 · (0.25 + 0.75 · 1.125) = 1.6406`.

Wyniki:
- **Dok. 0:** dose `0.9808 · 1/2.4297 = 0.4037` + daily `0.1335 · 1/2.4297 = 0.0550` = **0.4586**
- **Dok. 1:** lisinopril `0.9808 · 1/2.6406 = 0.3714` + daily `0.1335 · 1/2.6406 = 0.0506` = **0.4220**
- **Dok. 2:** daily `0.0550` = **0.0550**

Co z tego widać:
- Dokumenty 0 i 1 mają po jednym rzadkim słowie z zapytania, ale dokument 0 wygrywa, bo jest **krótszy** (normalizacja długości).
- `daily` jest w każdym dokumencie, więc prawie nic nie wnosi (niskie IDF).
- BM25 nie rozumie, że pytanie o lisinopril powinno raczej wskazać dokument 1. Liczy tylko słowa. Takie przypadki poprawia połączenie z wyszukiwaniem wektorowym (RRF).

#### Jak liczy to bm25s i dlaczego jest szybkie

Klasyczne implementacje (np. `rank_bm25`) liczą wzór dla każdego dokumentu przy każdym zapytaniu. `bm25s` robi to **z góry**: przy `index()` oblicza `IDF · TF_part` dla każdej pary (token, dokument), w której token występuje, i zapisuje to w **macierzy rzadkiej** (tokeny × dokumenty; większość komórek to zera, więc przechowywane są tylko niezerowe). Zapytanie sprowadza się wtedy do zsumowania wierszy macierzy dla tokenów z zapytania i wybrania k największych wyników. Dlatego w ewaluacji BM25 zajmuje ok. 1–2 ms na zapytanie.

Konsekwencja: wyniki zależą od całego zbioru (N, df, avgdl), więc po dodaniu albo usunięciu dokumentu indeks trzeba przebudować.

#### Mocne i słabe strony

| Mocne | Słabe |
|---|---|
| Dokładne terminy: nazwy leków, kody, liczby (np. `lisinopril`, `500`) | Nie zna synonimów ani parafraz: „good cholesterol” nie znajdzie „HDL” |
| Brak modelu, brak GPU, milisekundy na zapytanie | Wrażliwy na formę słowa (bez stemmingu `doses` ≠ `dose`) |
| Przewidywalny i łatwy do wytłumaczenia | Pomija pojedyncze znaki i stopwords (`1 g`, `C`) |
| Dobrze działa od razu, bez trenowania | Nie rozumie języka pytania ani kontekstu |

Wyszukiwanie wektorowe ma odwrotny profil, dlatego docagent łączy oba (sekcja niżej).

#### W docagent

`backend/src/docagent/search/bm25.py`, klasa `BM25Index`:
- **`rebuild(session)`** pobiera wszystkie chunki z bazy (posortowane po `id`), tokenizuje je (`stopwords="en"`) i buduje nowy `bm25s.BM25()` z domyślnymi `k1 = 1.5`, `b = 0.75`. Wywoływane przy starcie aplikacji (`lifespan`), po przetworzeniu każdego dokumentu (`process_document`) i po usunięciu dokumentu. Pozycja w indeksie odpowiada pozycji na liście `_chunk_ids`, co pozwala zamienić wynik bm25s na `chunk_id` z bazy.
- **Podmiana pod lockiem:** nowy indeks budowany jest poza lockiem, a lock (`threading.Lock`) obejmuje tylko podmianę referencji. Zapytania obsługiwane równolegle w innych wątkach widzą albo stary, albo nowy indeks, nigdy stan pośredni.
- **`search(query, k)`** tokenizuje zapytanie tak samo jak dokumenty (`return_ids=False` daje listę słów). Jeśli po tokenizacji nic nie zostało (np. same stopwords: „the of a”), zwraca pustą listę. Inaczej wywołuje `retrieve` z `k` ograniczonym do liczby chunków i odrzuca wyniki z wynikiem 0 (dokumenty bez żadnego słowa z zapytania).
- **Indeks w pamięci** wystarcza dla tysięcy chunków. Przy dużym zbiorze lepszy byłby indeks trwały albo przyrostowy, np. pełnotekstowe wyszukiwanie Postgresa (`tsvector`) albo Elasticsearch/OpenSearch.

### Wyszukiwanie hybrydowe i RRF
**Definicja:** łączenie wyników wyszukiwania leksykalnego (BM25) i semantycznego (wektory), żeby system radził sobie i z dokładnymi terminami, i z parafrazami. **Reciprocal Rank Fusion** łączy rankingi, a nie wyniki: `score(d) = Σ 1 / (k + pozycja_d)`, zwykle k = 60. Dzięki temu nie trzeba kalibrować różnych skal (BM25 od 0 do ∞, cosinus od −1 do 1).
**W docagent:** `reciprocal_rank_fusion` i `search` w `backend/src/docagent/search/hybrid.py`. Z każdej metody pobierane jest `max(4·k, 20)` kandydatów, żeby fuzja i opcjonalny filtr po dokumencie miały z czego wybierać. Tryb (`hybrid`, `bm25`, `vector`) wybiera się w ustawieniach czatu (ikona ustawień nad rozmową) albo w `POST /api/search`.

### Metryki ewaluacji wyszukiwania
**Definicje** (dla jednego zapytania; wynik to średnia po zapytaniach):
- **hit@k**: 1, jeśli w top k jest choć jeden trafny wynik, inaczej 0.
- **Precision@k**: odsetek trafnych wyników w top k.
- **Recall@k**: odsetek wszystkich trafnych elementów, które znalazły się w top k.
- **MRR@k** (Mean Reciprocal Rank): 1 / pozycja pierwszego trafnego wyniku (0, jeśli brak w top k).
- **nDCG@k** (normalized Discounted Cumulative Gain): suma `1 / log2(pozycja + 1)` dla trafnych wyników, podzielona przez wartość dla idealnego rankingu. Nagradza trafienia wysoko na liście.
- **LLM-as-judge**: ocena jakości odpowiedzi przez inny model językowy. W projekcie celowo nieużywana; ewaluacja jest bez LLM-a, szybka i deterministyczna.

**W docagent:** `backend/src/docagent/eval/metrics.py` (funkcje generyczne z testami w `backend/tests/test_retrieval_math.py`), raport w `backend/src/docagent/eval/__main__.py`. Trafność to oczekiwana para (plik, strona); powtórzenia tej samej strony w wynikach są usuwane przed liczeniem. Przy jednym trafnym elemencie na pytanie Precision@5 ma maksimum 0,2, a Recall@k jest równy hit@k.

---

## 3. LLM i agent

### LLM, model instruct i model „myślący”
**Definicja:** duży model językowy generuje tekst token po tokenie. **Model instruct** jest dostrojony do wykonywania poleceń i odpowiada od razu. **Model myślący** (reasoning) najpierw generuje rozumowanie, a dopiero potem odpowiedź: jest dokładniejszy w trudnych zadaniach, ale wolniejszy.
**W docagent:** domyślny model to `qwen3:4b-instruct` (`LLM_MODEL` w `backend/src/docagent/config.py`). Wariant `qwen3:4b` zawsze rozumuje i był kilka razy wolniejszy. `strip_thinking` w `backend/src/docagent/llm.py` usuwa ewentualne bloki `<think>…</think>`, gdyby podpięto model myślący.

### Kwantyzacja
**Definicja:** zapis wag modelu z mniejszą precyzją (np. 4 bity zamiast 16), żeby model zajmował mniej pamięci i działał szybciej, kosztem niewielkiej utraty jakości. `Q4_K_M` to popularny 4-bitowy format GGUF używany przez llama.cpp i Ollamę.
**W docagent:** modele z Ollamy są skwantyzowane (`qwen3:4b-instruct` ma ok. 2,5 GB), dzięki czemu razem z modelem embeddingów mieszczą się w 8 GB VRAM karty RTX 4070.

### Ollama
**Definicja:** narzędzie do uruchamiania modeli lokalnie (na bazie llama.cpp): pobiera modele (`ollama pull`), ładuje je na GPU i wystawia HTTP API, w tym endpointy zgodne z OpenAI (`/v1/chat/completions`, `/v1/embeddings`).
**W docagent:** domyślny provider LLM-a i embeddingów (`http://localhost:11434/v1`). W docker-compose backend łączy się z Ollamą na hoście przez `host.docker.internal`, żeby korzystać z GPU.

### API zgodne z OpenAI
**Definicja:** de facto standardowy format żądań i odpowiedzi czatu (lista wiadomości z rolami, definicje narzędzi w JSON Schema) i embeddingów. Implementuje go wielu dostawców (np. Novita) i serwery lokalne, więc zmiana dostawcy to zmiana adresu, klucza i nazwy modelu.
**W docagent:** `backend/src/docagent/llm.py`: `ChatOpenAI` (LangChain) do czatu i oficjalny klient `openai` do embeddingów, oba z konfigurowalnym `base_url`. Konfiguracja przez `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `EMBED_*` (`backend/.env.example`).

### Tool calling (wywoływanie narzędzi)
**Definicja:** model dostaje opisy funkcji (nazwa, opis, schemat argumentów w JSON Schema) i zamiast tekstu może zwrócić żądanie wywołania funkcji z argumentami. Kod aplikacji wykonuje funkcję i odsyła wynik jako wiadomość narzędzia, a model kontynuuje. **`tool_choice`** pozwala wymusić użycie narzędzia, ale nie każdy serwer to obsługuje (Ollama go ignoruje).
**W docagent:** trzy narzędzia w `backend/src/docagent/agent/tools.py`:
- `search_documents(query, document_id?)`: wyszukiwanie w trybie i z liczbą fragmentów z ustawień czatu (domyślnie hybrydowe, 5 fragmentów).
- `list_documents()`: lista dokumentów z id i liczbą stron.
- `read_page(document_id, page)`: pełny tekst strony.

Ponieważ `tool_choice` nie działa, pierwsze wyszukiwanie wykonuje kod (węzeł `retrieve`), a nie model.

### Agent
**Definicja:** program, w którym LLM w pętli decyduje o kolejnych akcjach (np. wywołaniach narzędzi) na podstawie ich wyników, aż uzna zadanie za wykonane. Wzorzec „myśl → działaj → obserwuj” nazywa się **ReAct**. **Budżet kroków** chroni przed nieskończoną pętlą.
**W docagent:** pętla `agent ⇄ tools` w `backend/src/docagent/agent/graph.py`, budżet kroków `max_steps` z ustawień czatu (domyślnie `AGENT_MAX_STEPS` = 6), liczony tylko w bieżącej turze rozmowy. Po wyczerpaniu budżetu model jest wywoływany bez narzędzi i musi odpowiedzieć z tego, co zebrał.

### LangChain
**Definicja:** biblioteka z abstrakcjami do pracy z LLM-ami: wiadomości (`HumanMessage`, `AIMessage`, `ToolMessage`, `SystemMessage`), modele czatu z jednolitym interfejsem (`invoke`, `bind_tools`), narzędzia (`@tool`) z automatycznym generowaniem schematu argumentów.
**W docagent:**
- `@tool(description=...)` z argumentami typu `Annotated[typ, "opis"]` w `backend/src/docagent/agent/tools.py`; z tego powstaje JSON Schema wysyłany do modelu.
- `response_format="content_and_artifact"`: narzędzie zwraca parę (tekst dla modelu, obiekty dla kodu). Model widzi sformatowane fragmenty, a aplikacja dostaje obiekty `SearchHit` w `ToolMessage.artifact` i zwraca je jako źródła bez parsowania odpowiedzi modelu.
- `ChatOpenAI(...).bind_tools(TOOLS)` w `graph.py`.

### LangGraph
**Definicja:** biblioteka do budowy agentów jako grafów stanów. **Stan** to słownik współdzielony przez węzły (`MessagesState` trzyma listę wiadomości, a reducer `add_messages` dokleja nowe wiadomości zamiast nadpisywać listę). **Węzeł** to funkcja, która dostaje stan i zwraca aktualizację. **Krawędź** wyznacza następny węzeł; **krawędź warunkowa** wybiera go funkcją od stanu. `compile()` zamienia definicję w wykonywalny graf; `recursion_limit` ogranicza liczbę kroków.
**W docagent:** `build_graph` w `backend/src/docagent/agent/graph.py`:
- `START → retrieve → agent`, potem krawędź warunkowa `_route`: `tools`, jeśli ostatnia wiadomość modelu zawiera wywołania narzędzi, inaczej `END`; `tools → agent`.
- `_tools_node` wykonuje wywołania; nieznane narzędzie albo błędne argumenty wracają do modelu jako `ToolMessage` z opisem błędu, zamiast przerywać żądanie.
- **Ustawienia w konfiguracji grafu:** `run_agent` przekazuje `ChatOptions` (`backend/src/docagent/agent/options.py`) w `config["configurable"]`. Węzły dostają `RunnableConfig` jako drugi argument, a narzędzie `search_documents` ma parametr `config: RunnableConfig`, który LangChain wstrzykuje sam i ukrywa przed modelem. Dzięki temu ustawienia zmieniają się per żądanie, bez zmiennych globalnych.
- `run_agent` z nowych wiadomości buduje ślad (`ToolStep`: nazwa, argumenty, `automatic` dla pierwszego wyszukiwania, wynik tekstowy, fragmenty, `error`), łącząc wywołania z wynikami po `tool_call_id`, i mierzy czas (`duration_ms`).

### Prompt systemowy
**Definicja:** wiadomość z rolą `system`, która ustala zachowanie modelu w całej rozmowie.
**W docagent:** `SYSTEM_PROMPT` w `backend/src/docagent/agent/graph.py`: odpowiadaj tylko na podstawie fragmentów, cytuj `[filename, p. N]`, przyznaj, gdy odpowiedzi nie ma, odpowiadaj w języku pytania.

---

## 4. Backend

### Python 3.15 i typowanie
**Definicja:** wskazówki typów (`list[int]`, `str | None`) nie zmieniają działania programu, ale pozwalają narzędziom (mypy, IDE) wykrywać błędy. Składnia generyków PEP 695 (`def f[T](x: T) -> T`) definiuje parametr typu bezpośrednio w sygnaturze.
**W docagent:** cały backend jest otypowany; generyki PEP 695 w `backend/src/docagent/eval/metrics.py` (`def ndcg_at_k[T: Hashable](...)`). Wersja Pythona jest przypięta w `backend/.python-version` i `pyproject.toml` (`requires-python`).

### uv
**Definicja:** menedżer projektów i pakietów Pythona (Astral, napisany w Rust): instaluje interpretery, tworzy `.venv`, rozwiązuje zależności i zapisuje dokładne wersje w `uv.lock`.
**W docagent:** `backend/pyproject.toml` (zależności i konfiguracja narzędzi), `backend/uv.lock`. Komendy: `uv sync`, `uv add`, `uv run ...`. W CI i Dockerze `uv sync --locked`, więc instalowane są dokładnie wersje z lockfile'a.

### FastAPI
**Definicja:** framework webowy, który z funkcji Pythona z adnotacjami typów buduje endpointy HTTP: waliduje wejście i wyjście przez Pydantic i automatycznie generuje schemat **OpenAPI** (opis API w JSON) oraz dokumentację pod `/docs`.
**W docagent:**
- Endpointy w `backend/src/docagent/api/routes.py`: `GET /api/health`, `GET/POST /api/documents`, `GET/DELETE /api/documents/{id}`, `GET /api/documents/{id}/file` (oryginalny PDF jako `application/pdf`), `POST /api/search`, `GET /api/chat/options`, `POST /api/chat`.
- **Dependency injection:** `SessionDep = Annotated[Session, Depends(get_session)]` daje każdemu żądaniu sesję bazy, zamykaną po odpowiedzi.
- **lifespan** w `backend/src/docagent/main.py`: przy starcie migracje bazy i budowa indeksu BM25.
- `generate_unique_id_function` ustawia `operationId` na nazwę funkcji, dzięki czemu wygenerowany klient TypeScript ma nazwy `listDocuments`, `uploadDocument` itd.
- Kody odpowiedzi: `202` (upload przyjęty do przetwarzania), `204` (usunięto), `400` (nie PDF), `404`, `422` (błąd walidacji).
- `fastapi dev` uruchamia serwer z automatycznym przeładowaniem przy zmianie plików `.py`.

### Synchroniczność, async i zadania w tle
**Definicja:** endpoint `async def` działa w pętli zdarzeń i nie może wykonywać blokujących operacji; endpoint `def` FastAPI uruchamia w puli wątków, więc może blokować (np. synchroniczny sterownik bazy). **BackgroundTasks** to mechanizm FastAPI wykonujący funkcję po wysłaniu odpowiedzi, w tym samym procesie. **Kolejka zadań** (np. Celery albo arq z brokerem Redis) przenosi pracę do osobnych procesów-workerów, z ponawianiem i przetrwaniem restartu serwera.
**W docagent:** endpointy są `def` (SQLAlchemy, pdfplumber i Tesseract są synchroniczne); `lifespan` jest async. Upload używa `BackgroundTasks` (`routes.py` → `process_document` w `pipeline.py`), więc odpowiedź przychodzi w milisekundach, a OCR i embeddingi liczą się po niej. Status dokumentu (`processing`/`ready`/`failed`) jest w bazie. Kolejki z workerami projekt nie używa; przy restarcie serwera w trakcie przetwarzania dokument zostałby w stanie `processing`.

### Pydantic v2 i pydantic-settings
**Definicja:** Pydantic waliduje i konwertuje dane na podstawie klas z adnotacjami typów (`BaseModel`); `Field(...)` dodaje ograniczenia i wartości domyślne (`default_factory` tworzy nową listę dla każdej instancji), `ConfigDict(from_attributes=True)` pozwala tworzyć model z dowolnego obiektu z atrybutami (np. obiektu ORM). Domyślnie Pydantic działa w trybie **lax** i konwertuje zgodne wartości (np. `"5"` → `5`); tryb **strict** (`ConfigDict(strict=True)`) przyjmuje tylko dokładnie zadeklarowane typy. W odróżnieniu od `dataclass`, model Pydantic sprawdza typy w czasie działania i rzuca `ValidationError`. pydantic-settings wczytuje konfigurację ze zmiennych środowiskowych i pliku `.env` z typami i wartościami domyślnymi.
**W docagent:**
- Schematy API w `backend/src/docagent/api/schemas.py`: `SearchRequest` (`query` min. 1 znak, `k` od 1 do 50, `mode` jako `Literal`), `DocumentOut` z `status: Literal["processing", "ready", "failed"]`, `ChatRequest` z historią.
- Modele wewnętrzne w trybie strict: `PageText` (`ingest/pdf.py`), `SearchHit` (`search/hybrid.py`), `ToolStep` i `AgentResult` (`agent/graph.py`). Błędny typ, np. numer strony jako tekst, zatrzymuje program w miejscu powstania, a nie dopiero w odpowiedzi API.
- `Settings` w `backend/src/docagent/config.py`, cache'owane przez `lru_cache`. Klucze API (`llm_api_key`, `embed_api_key`) mają typ `SecretStr`: przy wypisaniu albo w logach pokazują się jako `**********`, a prawdziwą wartość zwraca dopiero `get_secret_value()`.

---

## 5. Baza danych

### PostgreSQL i psycopg
**Definicja:** PostgreSQL to relacyjna baza danych z rozszerzeniami. psycopg 3 to sterownik Pythona do PostgreSQL.
**W docagent:** obraz `pgvector/pgvector:pg17` w `docker-compose.yml` (port 5433 na hoście). Tabele: `documents` (plik, liczba stron, strony OCR, status, błąd), `pages` (pełny tekst stron dla `read_page`), `chunks` (tekst, numer strony, embedding). Klucze obce z `ON DELETE CASCADE`, więc usunięcie dokumentu usuwa jego strony i chunki.

### pgvector i indeks HNSW
**Definicja:** pgvector to rozszerzenie PostgreSQL z typem `vector(n)` i operatorami odległości. **HNSW** (Hierarchical Navigable Small World) to indeks przybliżonego wyszukiwania najbliższych sąsiadów: wielopoziomowy graf, po którym wyszukiwanie przechodzi od ogólnych do szczegółowych połączeń. Jest bardzo szybki kosztem minimalnej utraty dokładności. `vector_cosine_ops` buduje indeks dla odległości cosinusowej.
**W docagent:** kolumna `Vector(768)` i indeks `chunks_embedding_hnsw` w `backend/src/docagent/db.py` oraz w migracji `0001_initial.py`.

### SQLAlchemy 2
**Definicja:** ORM i toolkit SQL dla Pythona. W stylu 2.0 modele deklaruje się przez `DeclarativeBase`, `Mapped[typ]` i `mapped_column`, a zapytania przez `select()`. **Sesja** to jednostka pracy: śledzi zmiany obiektów i zapisuje je przy `commit()`.
**W docagent:** `backend/src/docagent/db.py`: modele `Document`, `Page`, `Chunk` z relacjami (`cascade="all, delete-orphan"`), `engine` z `pool_pre_ping`, fabryka sesji `SessionLocal`. Zapytania z joinami i filtrem `in_` w `search/hybrid.py`.

### Alembic
**Definicja:** narzędzie do migracji schematu bazy dla SQLAlchemy. Każda migracja to plik z funkcjami `upgrade()` i `downgrade()` oraz identyfikatorem wersji wskazującym na poprzednią, co tworzy łańcuch wersji. Baza zapamiętuje bieżącą wersję w tabeli `alembic_version`. `alembic check` porównuje modele z bazą i zgłasza niezmigrowane różnice.
**W docagent:**
- Migracje w `backend/src/docagent/migrations/versions/`: `0001_initial.py` (rozszerzenie `vector`, tabele, indeks HNSW) i `0002_document_status.py` (kolumny `status` i `error`; istniejące wiersze dostają `ready`), `0003_document_file.py` (oryginalny plik `documents.content` jako `bytea` i flaga `pages.ocr`; migracja danych ustawia `ocr` dla dokumentów, w których wszystkie strony były z OCR).
- `content` jest kolumną **deferred**: lista dokumentów jej nie pobiera, a `has_file` to `column_property` (`content IS NOT NULL`) liczone w SQL, bez ładowania pliku.
- Migracje są częścią pakietu `docagent` (`script_location = "docagent:migrations"` w `pyproject.toml`), więc trafiają też do obrazu Dockera.
- `init_db()` w `db.py` uruchamia `alembic upgrade head` przy starcie aplikacji, w CLI ingestu i w testach.
- Nowa migracja: `cd backend && uv run alembic revision --autogenerate -m "opis"`.

---

## 6. Testy i jakość kodu

### pytest
**Definicja:** framework testów dla Pythona. Test to funkcja `test_*` z `assert`. **Fixture** to funkcja przygotowująca zasób dla testu (wstrzykiwana po nazwie argumentu), z zakresem (`function`, `session`) i sprzątaniem po `yield`. Plik `conftest.py` udostępnia fixtures wszystkim testom w katalogu. **Mock** (atrapa) zastępuje prawdziwą zależność kontrolowaną wersją; `monkeypatch` podmienia atrybuty na czas testu. **Test jednostkowy** sprawdza pojedynczą funkcję bez infrastruktury; **test integracyjny** sprawdza współpracę z prawdziwą bazą lub HTTP.
**W docagent** (`backend/tests/`, 36 testów):
- `conftest.py`:
  - ustawia `DATABASE_URL` na osobną bazę `docagent_test` przed importem aplikacji;
  - `database` (zakres sesji): tworzy bazę testową, jeśli jej nie ma, i uruchamia migracje; gdy Postgres jest niedostępny, testy integracyjne są pomijane;
  - `db`: sesja, a po teście `TRUNCATE ... RESTART IDENTITY CASCADE` i przebudowa BM25, więc każdy test startuje z pustą bazą;
  - `client`: `TestClient` FastAPI;
  - `no_network_embeddings` (autouse): mock embeddingów deterministycznym wektorem z hashy słów, więc żaden test nie łączy się z Ollamą;
  - `sample_pdf`, `scanned_pdf`: ścieżki do przykładowych PDF-ów.
- `test_api.py`: testy API przez `TestClient`, czyli upload i przetwarzanie w tle, OCR skanu, uszkodzony PDF → `failed`, odrzucenie nie-PDF, usuwanie (204/404), wyszukiwanie we wszystkich trybach, walidacja (422), szczegóły dokumentu ze stronami i flagą OCR, zwrot oryginalnego PDF-a i 404 dla dokumentu bez zapisanego pliku.
- `test_agent.py`: `FakeChatModel` zastępuje LLM i zwraca zaplanowane odpowiedzi. Testy sprawdzają, że agent najpierw szuka, potem woła `read_page`, że po wyczerpaniu budżetu dostaje model bez narzędzi, że nieznane narzędzie wraca do modelu jako błąd, że ślad zawiera argumenty, fragmenty i wyniki, że ustawienia zmieniają tryb i liczbę fragmentów, a endpoint `/api/chat` przekazuje historię i ustawienia, zwraca domyślne ustawienia i odrzuca wartości spoza zakresu (422).
- `test_models.py`: modele wewnętrzne odrzucają dane złego typu (`ValidationError`).
- `test_chunking.py`, `test_retrieval_math.py`, `test_pdf.py`: testy jednostkowe.

### TestClient
**Definicja:** klient HTTP z FastAPI/Starlette (oparty na `httpx`), który wywołuje aplikację w pamięci, bez uruchamiania serwera. Uruchamia `lifespan` i zadania w tle przed zwróceniem odpowiedzi.
**W docagent:** fixture `client` w `backend/tests/conftest.py`; dzięki wykonaniu `BackgroundTasks` test widzi dokument już przetworzony.

### Pokrycie kodu (pytest-cov / coverage.py)
**Definicja:** pomiar, które linie kodu zostały wykonane podczas testów. Raport `term-missing` pokazuje niepokryte linie. Próg (`--cov-fail-under`) przerywa build, gdy pokrycie spadnie.
**W docagent:** `[tool.coverage.run]` w `backend/pyproject.toml` (pomija migracje i skrypty CLI). Lokalnie `uv run pytest --cov` (obecnie ok. 95%); w CI próg 90%.

### ruff
**Definicja:** linter i formatter Pythona (Astral, Rust). Linter wykrywa błędy i złe praktyki według reguł; formatter ujednolica styl.
**W docagent:** `[tool.ruff]` w `backend/pyproject.toml`: długość linii 100, reguły E/F (pycodestyle, pyflakes), I (sortowanie importów), UP (nowoczesna składnia), B (bugbear). W CI `ruff check` i `ruff format --check`.

### mypy
**Definicja:** statyczny analizator typów. Sprawdza bez uruchamiania kodu, czy typy się zgadzają. Tryb `strict` wymaga typów we wszystkich funkcjach i zabrania m.in. niejawnego `Any`. Plugin Pydantic rozumie modele Pydantic.
**W docagent:** `[tool.mypy]` w `backend/pyproject.toml` (`strict = true`, `plugins = ["pydantic.mypy"]`; biblioteki bez typów oznaczone `ignore_missing_imports`). `uv run mypy` sprawdza `src/`; w CI osobny krok.

---

## 7. Frontend

### React 19 i TypeScript
**Definicja:** React to biblioteka do budowy interfejsów z komponentów (funkcji zwracających JSX). Stan komponentu trzyma `useState`, efekty uboczne (pobieranie danych, timery) `useEffect`, a odwołania do elementów DOM `useRef`. **Własny hook** to funkcja `useCoś`, która łączy wbudowane hooki w logikę wielokrotnego użytku; komponent, który z niego korzysta, zajmuje się tylko wyświetlaniem. `FC<Props>` (FunctionComponent) to typ komponentu z określonymi propsami. TypeScript dodaje do JavaScriptu statyczne typy sprawdzane przy budowaniu.
**W docagent** (`frontend/src/`):
- **Konwencje:** komponenty to stałe strzałkowe `export const Nazwa: FC<NazwaProps> = (...) => …`, propsy opisane osobnym `interface NazwaProps`. Wszystkie funkcje są strzałkowe.
- **Logika w hookach** (`hooks/`):
  - `useChat`: historia tur, wysyłanie pytania z ustawieniami, czyszczenie rozmowy, stan oczekiwania i błędu;
  - `useChatOptions`: domyślne ustawienia z API i zmiany użytkownika zapamiętywane w `localStorage`;
  - `useDocument`: szczegóły jednego dokumentu do podglądu;
  - `useDocuments`: lista, upload, usuwanie, odświeżanie co 1,5 s, dopóki jakiś dokument ma status `processing` (jeden `useEffect` z `setTimeout` obsługuje też pierwsze pobranie listy);
  - `useAutoResize`: dopasowanie wysokości pola czatu do treści.
- **Czyste funkcje i stałe** w `lib/`: `toHistory` (tury → historia dla API), `errorMessage` (czytelny tekst błędu z odpowiedzi FastAPI), tryby wyszukiwania i limity ustawień (`chatOptions.ts`), podpowiedzi dla narzędzi (`steps.ts`), adres pliku dokumentu (`documents.ts`).
- **Komponenty** w `components/`, pogrupowane według funkcji: `chat/` (`ChatPanel`, `ChatToolbar`, `ChatSettings`, `SearchModeSetting`, `NumberSetting`, `ChatInput`, `TurnView`, `TurnMeta`, `AgentTrace`, `StepView`, `UserBubble`), `documents/` (`DocumentsPanel`, `UploadButton`, `DocumentsTable`, `DocumentRow`, `StatusBadge`, `DocumentPreview`, `PdfFrame`, `PageList`), `shared/` (`ErrorAlert`, `HitCard`, `Tip`). Panele łączą hook z komponentami, a lokalny stan formularza (treść pola) zostaje w komponencie, który go wyświetla.
- `App.tsx`: zakładki Chat i Documents.
- **Tooltipy zamiast tekstów pomocniczych:** każdy element interfejsu (zakładki, przyciski, pola, odznaki, nagłówki kolumn, kroki agenta) jest owinięty w `Tip` (`components/shared/Tip.tsx`), który pokazuje opis z `en.json` (klucze `*.tip`). Na ekranie nie ma osobnych akapitów z instrukcjami.
- Ikony z `lucide-react` (licencja ISC).

TypeScript jest w wersji 6.0, bo generator klienta korzysta z JS-owego API kompilatora, którego nie ma TypeScript 7.

### Prettier i EditorConfig
**Definicja:** Prettier to formatter kodu: przepisuje plik do jednego, ustalonego stylu, więc spory o formatowanie znikają, a diffy pokazują tylko zmiany treści. EditorConfig (`.editorconfig`) mówi edytorom, jakie wcięcia i końce linii stosować już przy pisaniu.
**W docagent:** `frontend/.prettierrc.json` (wcięcie 4, bez średników, pojedyncze cudzysłowy, linie do 100 znaków; `package.json` z wcięciem 2, bo tak zapisuje go Yarn), `frontend/.prettierignore` (pomija wygenerowany klient `src/client` i `openapi.json`), `frontend/.editorconfig`. Komendy: `yarn format` i `yarn format:check`, ta druga także w CI.

### Chakra UI v3
**Definicja:** biblioteka gotowych komponentów React (przyciski, tabele, zakładki, alerty) z systemem tokenów stylu (`color="fg.muted"`, `colorPalette="red"`). Wersja 3 używa komponentów złożonych, np. `Tabs.Root`, `Tabs.List`, `Tabs.Trigger`, `Tabs.Content`.
**W docagent:** `ChakraProvider value={defaultSystem}` w `frontend/src/main.tsx`; komponenty `Tabs`, `Table`, `Card`, `Badge`, `Spinner`, `Collapsible`, `Alert`, `Tooltip`, `Popover` (ustawienia czatu), `SegmentGroup` (tryb wyszukiwania), `NumberInput`, `Field`, `Timeline` (kroki agenta), `Drawer` (podgląd dokumentu) i `Code` w `frontend/src/components/`.

### Internacjonalizacja (react-intl / FormatJS)
**Definicja:** i18n (internationalization) oddziela teksty interfejsu od kodu, żeby aplikację dało się przetłumaczyć bez zmian w komponentach. react-intl to biblioteka z rodziny FormatJS: `IntlProvider` udostępnia aktywny język i słownik komunikatów, `<FormattedMessage id="…" />` wstawia tekst w JSX, a `useIntl().formatMessage(...)` zwraca string tam, gdzie potrzebny jest zwykły tekst (`placeholder`, `aria-label`). Komunikaty używają składni **ICU MessageFormat**: zmienne `{filename}`, liczba mnoga `{count, plural, one {# source} other {# sources}}` z regułami dla danego języka. `FormattedDate` i `FormattedTime` formatują daty zgodnie z językiem.
**W docagent:**
- Słownik angielski: `frontend/src/i18n/messages/en.json`. Klucze są pogrupowane prefiksem obszaru (`app.*`, `chat.*`, `documents.*`, `search.*`, `hit.*`).
- `frontend/src/i18n/index.ts`: mapa `MESSAGES`, typ `MessageId` wyliczany z kluczy `en.json` i `detectLocale()`, który wybiera język z `navigator.languages`, a gdy go nie ma, używa angielskiego.
- **Typowane identyfikatory:** deklaracja `FormatjsIntl.Message` sprawia, że literówka w `id` jest błędem kompilacji TypeScriptu. `satisfies Record<string, Record<MessageId, string>>` wymusza, żeby każdy dodany język miał wszystkie klucze.
- `IntlProvider` w `frontend/src/main.tsx` obejmuje całą aplikację.
- Komponenty nie zawierają tekstów na sztywno. Także listy (kolumny tabeli, tryby wyszukiwania w `lib/chatOptions.ts`, podpowiedzi narzędzi w `lib/steps.ts`) trzymają identyfikatory komunikatów, a nie gotowe napisy.
- **Nowy język, np. polski:** skopiować `en.json` do `pl.json`, przetłumaczyć wartości, dopisać `pl` do `MESSAGES` w `index.ts`. Przeglądarka z językiem polskim dostanie go automatycznie.

### Vite
**Definicja:** narzędzie do budowania frontendu. W trybie dev serwuje moduły ES bezpośrednio przeglądarce i ma **HMR** (Hot Module Replacement), czyli podmianę zmienionego modułu bez przeładowania strony. `vite build` tworzy zoptymalizowaną paczkę produkcyjną. **Proxy** dev servera przekazuje wybrane ścieżki do innego serwera.
**W docagent:** `frontend/vite.config.ts`: plugin React i proxy `/api` → `http://localhost:8000`, więc frontend i backend działają razem bez konfiguracji CORS.

### Yarn 4 i corepack
**Definicja:** Yarn to menedżer pakietów JavaScript; `yarn.lock` przypina dokładne wersje. Corepack (część Node.js) instaluje wersję menedżera wskazaną w polu `packageManager` w `package.json`. `nodeLinker: node-modules` każe Yarnowi tworzyć klasyczny katalog `node_modules`.
**W docagent:** `frontend/package.json` (`packageManager: yarn@4.18.1`), `frontend/.yarnrc.yml`, `frontend/yarn.lock`. W CI `yarn install --immutable` przerywa build, jeśli lockfile nie zgadza się z `package.json`.

### Generowanie klienta API z OpenAPI (hey-api)
**Definicja:** z opisu OpenAPI generuje się kod klienta: funkcje dla endpointów i typy dla żądań i odpowiedzi. Frontend nie może wtedy wywołać nieistniejącego endpointu ani pomylić pól, bo kompilator TypeScript to wykryje.
**W docagent:**
- `yarn gen:api` eksportuje schemat z FastAPI (`backend/src/docagent/export_openapi.py`) do `frontend/openapi.json`, a `@hey-api/openapi-ts` (`frontend/openapi-ts.config.ts`) generuje `frontend/src/client/`.
- Komponenty i hooki importują np. `listDocuments`, `getDocument`, `uploadDocument`, `defaultChatOptions`, `chat` i typy `DocumentOut`, `DocumentDetail`, `ChatOptions`, `AgentResult`, `ToolStep`, `SearchHit`.
- Funkcje zwracają `{ data, error }`; błąd walidacji z FastAPI (`detail`) jest wyświetlany przez `ErrorAlert`.

### oxlint
**Definicja:** szybki linter JavaScript/TypeScript (Rust), zgodny z regułami ESLint, w tym regułami React.
**W docagent:** `yarn lint` (`frontend/.oxlintrc.json`), uruchamiany w CI.

---

## 8. Infrastruktura i CI/CD

### Docker i obraz wieloetapowy
**Definicja:** Docker pakuje aplikację z zależnościami w obraz uruchamiany jako kontener. **Build wieloetapowy** (multi-stage) używa ciężkiego etapu do budowania i kopiuje do lekkiego obrazu końcowego tylko wynik. `.dockerignore` wyklucza pliki z kontekstu budowania.
**W docagent:** `backend/Dockerfile`:
- etap `build`: `python:3.15-slim` + `build-essential` (część zależności nie ma jeszcze gotowych wheeli dla Pythona 3.15 i musi się skompilować) + `uv sync --locked --no-dev`;
- etap końcowy: `python:3.15-slim` + Tesseract + skopiowany `.venv`, start przez `uvicorn docagent.main:app`.

Kolejność `COPY pyproject.toml uv.lock` przed `COPY src` sprawia, że warstwa z zależnościami jest cache'owana, gdy zmienia się tylko kod. `backend/.dockerignore` wyklucza `.venv`, cache i `.env`.

### Docker Compose
**Definicja:** opis wielu kontenerów (usług), ich portów, wolumenów, zmiennych środowiskowych i zależności w jednym pliku YAML. **Healthcheck** określa, kiedy usługa jest gotowa; `depends_on` z `condition: service_healthy` czeka na tę gotowość. **Profile** pozwalają uruchamiać część usług tylko na żądanie.
**W docagent:** `docker-compose.yml`:
- `db` (pgvector, wolumen `pgdata`, healthcheck `pg_isready`);
- `backend` w profilu `full` (`docker compose --profile full up --build`), łączy się z bazą po nazwie usługi `db` i z Ollamą na hoście przez `host.docker.internal`.

### GitHub Actions
**Definicja:** CI/CD wbudowane w GitHuba. **Workflow** (YAML w `.github/workflows/`) uruchamia się na zdarzeniach (push, pull request). Składa się z **jobów** (równoległych maszyn), te z **kroków** (komendy albo gotowe akcje, np. `actions/checkout`). **services** uruchamiają kontenery pomocnicze (np. bazę) obok joba; `needs` ustala kolejność jobów; cache przyspiesza kolejne przebiegi.
**W docagent:** `.github/workflows/ci.yml`:
- `backend`:
  - Postgres z pgvector jako service, Tesseract, `uv sync --locked`;
  - `ruff check`, `ruff format --check`, `mypy`;
  - `pytest` z pokryciem (próg 90%);
  - `alembic check` (czy modele zgadzają się z migracjami);
  - kontrola, czy `frontend/openapi.json` zgadza się z aktualnym API.
- `frontend`: `yarn install --immutable`, ponowne wygenerowanie klienta i `git diff --exit-code` (czy klient w repo jest aktualny), `yarn lint`, `yarn build`.
- `docker`: po udanym `backend` buduje obraz backendu (`docker/build-push-action`, bez publikacji, z cache GitHub Actions).

---

## 9. Licencje

**Definicja:** licencje **permisywne** (MIT, Apache 2.0, BSD) pozwalają używać kodu w produktach komercyjnych i zamkniętych, wymagając głównie zachowania informacji o autorach. Licencje **copyleft** (GPL, AGPL) wymagają udostępnienia kodu dzieł zależnych; AGPL dotyczy także oprogramowania udostępnianego przez sieć. **LGPL** pozwala używać biblioteki w zamkniętym produkcie, o ile nie modyfikuje się samej biblioteki.
**W docagent:** zależności są na licencjach permisywnych lub LGPL (psycopg); świadomie nie użyto PyMuPDF (AGPL). Do PDF-ów służą pdfplumber (MIT) i pypdfium2 (Apache/BSD), do OCR Tesseract (Apache 2.0). Projekt ma licencję MIT (`LICENSE`).
