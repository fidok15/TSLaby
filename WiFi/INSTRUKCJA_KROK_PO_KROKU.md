# Lab Wi-Fi: instrukcja krok po kroku (na 5.0)

## Podział ról (trzymajcie się go przez cały lab)

| | **Osoba A (Ty)** | **Osoba B (Kolega)** |
|---|---|---|
| Komputer | **PC1** | **PC2** |
| Router | **R1** (główny, z Internetem) | **R2** (później Media Bridge) |
| Karta | USB-AX56 nr 1 | USB-AX56 nr 2 |

**Zasada złota:** routery konfigurujesz **przez kabel LAN**, a łącze Wi-Fi testujesz **po wypięciu kabla**.
**Zrzuty ekranu:** `Win + Shift + S`. Róbcie ich dużo, każdy od razu zapisujcie z nazwą typu `z2_kanal7_ping.png`.

### Przydatne do sprawdzenia, jak połączona jest karta Wi-Fi
```
netsh wlan show interfaces
```
To polecenie pokazuje SSID, `Typ radia` (np. 802.11ax), kanał i prędkość. Świetnie się nadaje na zrzut do zadania 3.

---

## Przygotowanie (OBAJ, każdy na swoim stanowisku)

1. Rozpakujcie `Wi-Fi-20261126.zip` na pulpit. Potrzebny będzie `Settings_RT-AX86S.CFG` i `iperf2.exe`.
2. Wepnij kartę USB-AX56 do komputera.
3. `Win + X` → **Menedżer urządzeń** → **Karty sieciowe**. Ma tam być karta ASUS USB-AX56. **Zrzut.**
   - Jeśli jej nie ma, karta ma wbudowany instalator sterownika (pojawi się jak pendrive) albo instalujecie sterownik z płyty/strony ASUS.
4. Router:
   1. Przykręć 3 anteny.
   2. Podłącz zasilacz i włącz router przyciskiem.
   3. Kabel z gniazdka sieciowego w sali wepnij do **niebieskiego** portu (WAN).
   4. Kabel od komputera wepnij do **żółtego** portu (LAN 1–4).
5. `Win + R` → `cmd` → `ipconfig`. Odczytaj **Brama domyślna** (zwykle `192.168.50.1`).
6. Wpisz ten adres w przeglądarce. Jeśli wyskoczy kreator, przeklikaj go albo zaloguj się.
7. Opcjonalnie: przełącz język na **English** (prawy górny róg).
8. Wgraj konfigurację: **Advanced Settings → Administration → zakładka Restore/Save/Upload Setting → Restore Setting → Upload** → wybierz `Settings_RT-AX86S.CFG`. Poczekaj ok. 1 minuty.
9. Zaloguj się ponownie: `admin` / `admin_password`.
10. **Advanced Settings → Wireless → General** → zmień nazwę sieci (Network Name/SSID) z `student_grupaX` na numer waszej grupy, np. `student_grupa3`. **Apply.**
    - **A:** `student_grupa3`
    - **B:** na R2 na razie też ustaw swoją nazwę, np. `student_grupa3_2`, żeby się nie myliło.

---

## Zadanie 1: Zabezpieczenie sieci (3.0)

**B:** wyłącz R2 przyciskiem zasilania. Ten router w tym zadaniu nie jest używany.

**A (na R1, przez kabel):**
1. Sprawdź adres MAC obu kart USB. Na **każdym** PC: `cmd` → `ipconfig /all` → sekcja karty Wi-Fi (ASUS USB-AX56) → **Adres fizyczny**, np. `A1-B2-C3-D4-E5-F6`. B dyktuje swój adres Tobie.
2. **Advanced Settings → Wireless → General:**
   - **Hide SSID** → `Yes`
   - **Authentication Method** → `WPA3-Personal`
   - **WPA Pre-Shared Key** → `student_password`
   - **Apply.** Jeśli jest Smart Connect, ustawienia obowiązują dla wszystkich pasm.
3. **Advanced Settings → Wireless → zakładka Wireless MAC Filter:**
   - **Enable MAC Filter** → `Yes`
   - **MAC Filter Mode** → `Accept`
   - Wpisz MAC karty A i kliknij `+`. Wpisz MAC karty B i kliknij `+`.
   - **Apply.**
4. **Zrzuty** wszystkich trzech ustawień (ukryte SSID, WPA3, lista MAC).

**OBAJ (łączenie z ukrytą siecią):**
1. A: wypnij kabel LAN z PC1. B: twój PC2 w ogóle nie ma kabla do R1.
2. Ikona Wi-Fi na pasku → przewiń na sam dół → **Ukryta sieć** → **Połącz**.
3. Nazwa: `student_grupa3` (nazwa z R1), hasło: `student_password`.
4. `ipconfig` → zapisz swój adres IPv4 i podaj go koledze.
5. Pingujcie się nawzajem:
   - A: `ping <IP_PC2>`
   - B: `ping <IP_PC1>`
   - **Zrzut** wyników pingów.
   - Jeśli ping nie przechodzi (`Upłynął limit czasu żądania`), to blokuje zapora Windows. Wpisz w PowerShell jako administrator:
     ```
     New-NetFirewallRule -DisplayName "ICMP" -Protocol ICMPv4 -IcmpType 8 -Action Allow
     ```
     Możesz też na czas laba wyłączyć zaporę.

**Pokaż prowadzącemu:** ustawienia routera i działający ping.

**Sprzątanie:** A wpina kabel z powrotem i wgrywa `Settings_RT-AX86S.CFG` jeszcze raz (punkt 8 z przygotowania). Potem ustawia SSID jak w punkcie 10.

---

## Zadanie 2: Kanały i interferencje (3.5)

Teraz pracują **oba routery**, każdy na swoim. B: włącz R2.

**OBAJ, każdy na swoim routerze (przez kabel):**
1. **Advanced Settings → Wireless → General:**
   - **Smart Connect** → wyłącz (`Disable`), jeśli jest włączony.
   - **Band** → `2.4 GHz`
   - **Network Name (SSID):**
     - **A:** `student_grupa3`
     - **B:** `student_grupa3_2`
   - **Wireless Mode** → `Legacy`
   - **Apply.**
   - Opcjonalnie wyłącz sieć 5 GHz: **Wireless → Professional** → Band `5 GHz` → **Enable Radio** → `No`.
2. **Zrzut** ustawień.

**OBAJ (telefon):**
1. Zainstaluj aplikację **WiFi Analyzer** (Android) albo dowolny odpowiednik.
2. Zrób **zrzut** wykresu kanałów 2,4 GHz i 5 GHz.
3. Zanotuj odpowiedzi do raportu:
   - Które kanały są najbardziej zatłoczone? Zwykle 1, 6, 11 w paśmie 2,4 GHz.
   - Które kanały wybrać dla nowych AP? Te najmniej zajęte, a w 2,4 GHz tylko spośród niezachodzących na siebie 1/6/11. W 5 GHz jest dużo wolnego miejsca.

**OBAJ (test przed zmianą kanału):**
1. Wypnij kabel LAN.
2. Połącz się przez Wi-Fi z SSID swojego routera (A: `student_grupa3`, B: `student_grupa3_2`). Hasło: `student_password`.
3. Otwórz 2–3 karty z YouTube i włącz filmy w wysokiej jakości.
4. `cmd`:
   ```
   ping -n 100 192.168.50.1
   ```
   (albo adres bramy z `ipconfig`)
5. Poczekaj ok. 100 s. **Zrzut** podsumowania: ile pakietów utracono (%), czas min/maks/średni.

**OBAJ (zmiana na kanał 7):**
1. Wepnij kabel → strona routera → **Wireless → General** → **Control Channel** → `7` → **Apply.**
2. Wypnij kabel i połącz się znowu przez Wi-Fi.
3. Powtórz YouTube i `ping -n 100 192.168.50.1`. **Zrzut.**
4. Porównajcie. Na kanale 7 nadaje router prowadzącego, więc powinno być więcej strat i większe/skaczące czasy. Do raportu: interferencje współkanałowe i z sąsiednich kanałów, wspólne medium i CSMA/CA, czyli rywalizacja o dostęp do kanału.

**Pokaż prowadzącemu:** zrzuty przed/po z komentarzem.

**Sprzątanie:** oba routery z powrotem na `Settings_RT-AX86S.CFG`.

---

## Zadanie 3: Standardy Wi-Fi (4.0)

**B:** wyłącz R2 przyciskiem. Używamy tylko **R1**.

Podział: **A konfiguruje router (PC1 na kablu)**, **B testuje przez Wi-Fi (PC2 bez kabla, na karcie USB)**. Dzięki temu nikt nie przepina kabla w kółko. Jeśli prowadzący chce, żeby każdy coś zmierzył, zamieńcie się w połowie.

**A (na R1):**
1. **Advanced Settings → Wireless → General** → **Enable Smart Connect** → `Off`/`Disable` → **Apply.**
2. Band `2.4 GHz` → SSID `student_grupa3` → **Apply.**
3. Band `5 GHz` → SSID `student_grupa3_5` → **Apply.**

Teraz robicie 5 pomiarów. Dla **każdego** pomiaru:

| # | A ustawia na R1 (Wireless → General) | B łączy się z |
|---|---|---|
| a | Band `2.4 GHz` → Wireless Mode `Legacy` | `student_grupa3` |
| b | Band `2.4 GHz` → Wireless Mode `N only` | `student_grupa3` |
| c | Band `5 GHz` → Wireless Mode `Legacy` | `student_grupa3_5` |
| d | Band `5 GHz` → Wireless Mode `N/AC/AX mixed` | `student_grupa3_5` |
| e | Band `5 GHz` → Wireless Mode `AX only` + zaznacz **802.11ax / WiFi 6 mode** → `Enable` | `student_grupa3_5` |

**Procedura dla każdego wiersza:**
1. **A:** ustaw tryb → **Apply** → zrób **zrzut** ustawienia → powiedz „gotowe”.
2. **B:** rozłącz się z siecią i połącz ponownie (po zmianie trybu klient musi się połączyć od nowa).
3. **B:** sprawdź typ połączenia: **Ustawienia → Sieć i Internet → Wi-Fi → (nazwa sieci) właściwości**. Pole **Protokół** pokazuje np. `802.11g`, `Wi-Fi 4 (802.11n)` albo `Wi-Fi 6 (802.11ax)`. Możesz też użyć `netsh wlan show interfaces`. **Zrzut.**
4. **B:** wejdź na https://www.speedtest.net → **GO** → **zrzut** wyniku (Download/Upload/Ping).
5. Zapiszcie wyniki w tabelce.

Do raportu: wyniki powinny rosnąć mniej więcej w kolejności a < b < c < d ≈ e. Ograniczeniem może być łącze uczelni, a nie Wi-Fi. Napiszcie to, jeśli d i e wyjdą podobnie.

**Pokaż prowadzącemu:** pary zrzutów (Speedtest + Protokół z ustawień karty).

---

## Zadanie 4: Media Bridge (4.5)

**OBAJ:** wypnijcie karty USB Wi-Fi z komputerów. Wszystko idzie po kablach.

**A (R1):**
1. Wgraj `Settings_RT-AX86S.CFG` na R1 (jak w przygotowaniu, punkt 8). Smart Connect zostaje taki, jak w pliku.
2. R1 zostaje podłączony do Internetu niebieskim portem WAN.
3. Zapamiętaj SSID i hasło z R1 (`student_grupa3` / `student_password`). Dla sieci 5 GHz SSID może mieć inną nazwę. Sprawdź w **Wireless → General**.
4. Odepnij PC1 od R1. PC1 będzie podłączony do R2.

**B (R2), reset do ustawień fabrycznych:**
1. Włącz R2. Szpilką przytrzymaj przycisk **RESET** z tyłu przez ok. 5–10 s, aż dioda zasilania zacznie migać. Puść i poczekaj ok. 2–3 min.
   - Inny sposób: **Administration → Restore/Save/Upload Setting → Factory default → Restore**.
2. **Nic nie wpinaj do niebieskiego portu R2.**
3. Podłącz PC2 kablem do **żółtego** portu R2.
4. W przeglądarce wejdź na `http://router.asus.com` albo `192.168.50.1`. Uruchomi się kreator (QIS).

**B (kreator Media Bridge).** Szczegóły: https://www.asus.com/support/faq/1043884/
1. W kreatorze wybierz **Advanced Settings / Zaawansowane ustawienia** (nie „Create a new network”).
2. **Choose operation mode** → **Media Bridge** → Next.
3. Z listy sieci wybierz sieć R1 (najlepiej 5 GHz) → wpisz hasło `student_password` → Connect.
4. Ustawienia IP: **Automatic IP (DHCP)** → Next.
5. Ustaw login/hasło do panelu R2 (np. `admin` / `admin_password`) → Apply. Poczekaj, aż R2 się zrestartuje.
   - Jeśli nie ma kreatora, bo router już skonfigurowany: **Administration → Operation Mode → Media Bridge → Save** i dalej to samo.

**OBAJ:**
1. Podłączcie **PC1 i PC2 kablami do żółtych portów R2**.
2. `ipconfig` na obu. Adresy powinny być z puli R1, np. `192.168.50.x`, bo DHCP robi R1.
   - Jeśli adresy są dziwne, wpisz `ipconfig /release` i potem `ipconfig /renew`.
3. Pingujcie się nawzajem (`ping <IP drugiego PC>`) i sprawdźcie Internet (`ping 8.8.8.8` albo otwórzcie stronę). **Zrzuty.**

**Pokaż prowadzącemu:** działający układ, Internet i ping.

---

## Zadanie 5: Szerokość kanału a przepustowość (5.0)

Topologia: **PC1 –kabel– R1 ~~Wi-Fi~~ R2 –kabel– PC2**

**A:**
1. **Wypnij kabel WAN z R1** (bez Internetu).
2. Podłącz **PC1 kablem do żółtego portu R1**.
3. Wejdź na `192.168.50.1` (R1).
4. **Wireless → General**, Band `5 GHz`:
   - **Wireless Mode** → `AX only` + **802.11ax / WiFi 6 mode** → `Enable` (albo `Auto` z włączonym trybem AX, zależnie od tego, co prowadzący uzna)
   - **Control Channel** → `36`. Na kanałach 36–48 da się ustawić 160 MHz bez czekania na DFS.
5. `ipconfig` → podaj IP PC1 koledze.
6. Wypakuj `iperf2.exe`. W `cmd` przejdź do folderu, np. `cd %USERPROFILE%\Desktop`.
7. Uruchom **serwer** i zostaw okno otwarte:
   ```
   iperf2.exe -s -u -i 1
   ```
   Jeśli Windows zapyta o zaporę, kliknij **Zezwól**.

**B:**
1. PC2 zostaje na kablu do R2.
2. `ping <IP_PC1>`. Ma działać. **Zrzut.**
3. Wypakuj `iperf2.exe` i przejdź do folderu w `cmd`.

**Pomiary: 4 razy, dla każdej szerokości kanału.**

| # | A ustawia na R1: **Channel bandwidth** |
|---|---|
| a | `20 MHz` |
| b | `40 MHz` |
| c | `80 MHz` |
| d | `160 MHz` (w polu może być `20/40/80/160 MHz`; włącz też **Enable 160 MHz**, jeśli jest taka opcja) |

**Procedura dla każdego wiersza:**
1. **A:** ustaw szerokość → **Apply** → **zrzut** ustawienia. Poczekaj ok. 1 min, aż R2 się ponownie połączy (B sprawdza `ping <IP_PC1>`).
2. **B:** uruchom klienta:
   ```
   iperf2.exe -c <IP_PC1> -u -b 1000M -t 30 -i 1
   ```
   - `-b 1000M` jest ważne. Bez tego UDP wyśle tylko 1 Mb/s i każda szerokość da ten sam wynik.
   - Jeśli przy 160 MHz wynik dobija do ~1000 Mb/s, powtórz z `-b 2000M`.
3. **A i B:** **zrzut** okna iperf. Najważniejszy jest raport serwera (u A): wiersz końcowy z `Bandwidth`, `Jitter` i `Lost/Total`.
4. Zapiszcie w tabelce: szerokość → przepustowość, jitter, % strat.

Do raportu: szersza szerokość kanału = więcej podnośnych = większa przepustowość, mniej więcej ×2 przy każdym podwojeniu. Szerszy kanał jest jednak bardziej podatny na zakłócenia i ma mniejszy zasięg. Maksimum ogranicza też port Ethernet 1 Gb/s.

**Pokaż prowadzącemu:** ping, zrzuty iperf i ustawienia szerokości.

---

## Koniec

1. Odkręć anteny i odłącz kable oraz zasilacze.
2. Oddaj karty USB i routery prowadzącemu.
3. Raport (zrzuty + komentarze + odpowiedzi z zadania 2) wrzuć na ePortal.

## Ściąga: gdy coś nie działa

- **Nie mogę wejść na router:** sprawdź `ipconfig` → brama domyślna. Upewnij się, że kabel jest w **żółtym** porcie.
- **Ping nie działa:** zapora Windows (polecenie `New-NetFirewallRule` z zadania 1).
- **Nie widzę ukrytej sieci:** dodaj ją ręcznie przez „Ukryta sieć” i wpisz dokładną nazwę SSID.
- **Po zmianie trybu nie mogę się połączyć:** usuń sieć („Zapomnij”) i połącz się ponownie.
- **Media Bridge nie dostaje IP:** R1 musi mieć włączone DHCP (jest w pliku `.CFG`). Zrób `ipconfig /renew`.
- **160 MHz się nie włącza:** zmień Control Channel na `36` i poczekaj ok. 1 min (DFS).
