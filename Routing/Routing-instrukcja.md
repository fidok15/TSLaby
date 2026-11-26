# Temat 4: Routing — instrukcja krok po kroku

> Zamień `Nazwisko1` / `Nazwisko2` na swoje nazwiska.
> Adresy C/D/E oraz Loopback to propozycja, możesz je zmienić.
> Każdy wynik (ping, `show ip route`) zapisuj zrzutem ekranu albo logiem PuTTY, bo przyda się do sprawozdania.

---

## 0. Plan adresacji

| Sieć | Urządzenie / interfejs | Adres | Maska |
|---|---|---|---|
| A 10.0.1.0/24 | R1 G0/1 | 10.0.1.1 | 255.255.255.0 |
| A | PC1 | 10.0.1.254 (brama 10.0.1.1) | 255.255.255.0 |
| B 10.0.2.0/24 | R2 G0/1 | 10.0.2.1 | 255.255.255.0 |
| B | PC2 | 10.0.2.254 (brama 10.0.2.1) | 255.255.255.0 |
| C 172.16.3.0/30 | R1 S0/0/0 | 172.16.3.1 | 255.255.255.252 |
| C | R2 S0/0/0 | 172.16.3.2 | 255.255.255.252 |
| D 172.16.4.0/30 | R1 G0/0 | 172.16.4.1 | 255.255.255.252 |
| D | R3 G0/0 | 172.16.4.2 | 255.255.255.252 |
| E 172.16.5.0/30 | R2 S0/0/1 | 172.16.5.1 | 255.255.255.252 |
| E | R3 S0/0/1 | 172.16.5.2 | 255.255.255.252 |
| „Internet” | R1 Loopback0 | 8.8.8.8 | 255.255.255.255 |
| prywatna | R3 Loopback0 | 192.168.3.1 | 255.255.255.0 |

---

## 1. Okablowanie fizyczne (najpierw tylko R1 i R2)

Na tym etapie nie podłączaj jeszcze R3.

| Z | Do | Kabel |
|---|---|---|
| PC1 (karta sieciowa) | Switch A, dowolny port | prosty (straight-through, RJ45) |
| Switch A, dowolny port | R1 **G0/1** | prosty |
| PC2 (karta sieciowa) | Switch B, dowolny port | prosty |
| Switch B, dowolny port | R2 **G0/1** | prosty |
| R1 **S0/0/0** | R2 **S0/0/0** | szeregowy (serial, końcówki DCE/DTE) |
| PC1 (USB / COM) | R1 port **CONSOLE** | kabel konsolowy (niebieski rollover lub USB-console) |
| PC2 (USB / COM) | R2 port **CONSOLE** | kabel konsolowy |

- Kabel konsolowy jest niezależny od kabla Ethernet. PC1 może jednocześnie być w sieci A i mieć konsolę do R1.
- Na kablu szeregowym sprawdź, która końcówka ma napis **DCE**. Router od strony DCE musi mieć ustawiony `clock rate`.
- Switche nie wymagają konfiguracji (domyślnie VLAN 1). Wystarczy podłączyć kable.

---

## 2. Połączenie z routerem przez PuTTY

1. Podłącz kabel konsolowy: z PC do portu **CONSOLE** routera.
2. Sprawdź numer portu COM na PC:
   - Otwórz **Menedżer urządzeń** (`Win+X` → Menedżer urządzeń).
   - Rozwiń **Porty (COM i LPT)**.
   - Odczytaj numer, np. `COM3`. Przy USB-console może być potrzebny sterownik (Cisco USB Console).
3. Uruchom **PuTTY** i ustaw:
   - **Connection type:** `Serial`
   - **Serial line:** `COM3` (Twój numer)
   - **Speed:** `9600`
   - W zakładce *Connection → Serial*: Data bits `8`, Stop bits `1`, Parity `None`, Flow control `None`.
4. Włącz logowanie (ułatwia sprawozdanie):
   - Przejdź do *Session → Logging* i zaznacz **All session output**.
   - Wybierz plik, np. `R1_log.txt`.
5. Kliknij **Open** i naciśnij **Enter** kilka razy, aż pojawi się prompt `Router>`.
6. Jeżeli pojawi się pytanie `Would you like to enter the initial configuration dialog? [yes/no]:`, wpisz `no`.
7. Jeżeli router ma starą konfigurację, wyczyść ją (zrób to na każdym routerze):
   ```
   enable
   erase startup-config
   reload
   ```
   - Na pytanie o zapis konfiguracji (`System configuration has been modified. Save?`) odpowiedz **no**.
   - Potwierdź reload klawiszem **Enter**.
   - Po restarcie na pytanie o *initial configuration dialog* odpowiedz `no`.

**Ekran pusty?** Sprawdź COM, prędkość 9600 i Flow control None, potem naciśnij Enter. Możesz też przełożyć kabel do innego portu USB i ponownie sprawdzić numer COM.

### Przydatne komendy na start (każdy router)

```
enable
conf t
no ip domain-lookup        ! literówka nie zawiesza konsoli na DNS
line console 0
 logging synchronous       ! logi nie przerywają pisania
 exec-timeout 0 0          ! konsola się nie wylogowuje
 exit
end
terminal length 0          ! show bez "--More--"
```

---

## 3. Konfiguracja PC (Windows)

1. Wciśnij `Win+R`, wpisz `ncpa.cpl` i naciśnij Enter.
2. Kliknij prawym przyciskiem kartę podłączoną do switcha i wybierz *Właściwości*.
3. Wybierz **Protokół internetowy w wersji 4 (TCP/IPv4)** i kliknij *Właściwości*.
4. Wpisz ręcznie adresy:
   - **PC1:** IP `10.0.1.254`, maska `255.255.255.0`, brama `10.0.1.1`
   - **PC2:** IP `10.0.2.254`, maska `255.255.255.0`, brama `10.0.2.1`
5. Wyłącz zaporę Windows albo zezwól na ICMP. Bez tego ping PC↔PC nie działa.
   - Szybko: *Zapora Windows Defender → Włącz lub wyłącz* i wyłącz ją dla wszystkich profili.
   - Albo w cmd uruchomionym jako administrator:
     ```
     netsh advfirewall firewall add rule name="ICMP" protocol=icmpv4:8,any dir=in action=allow
     ```
6. Sprawdź ustawienia: `ipconfig` w cmd.

---

## 4. Zadanie 1 — podstawowa konfiguracja R1 i R2

### R1 (PuTTY z PC1)

```
enable
conf t
hostname R1_Nazwisko1
interface g0/1
 ip address 10.0.1.1 255.255.255.0
 no shutdown
 exit
interface s0/0/0
 ip address 172.16.3.1 255.255.255.252
 no shutdown
 exit
interface loopback0
 ip address 8.8.8.8 255.255.255.255
 exit
end
show controllers s0/0/0
```

- Jeżeli w wyniku `show controllers` jest `DCE`, ustaw zegar:
  ```
  conf t
  interface s0/0/0
   clock rate 64000
  end
  ```
- Jeżeli jest `DTE`, pomiń `clock rate`.

### R2 (PuTTY z PC2)

```
enable
conf t
hostname R2_Nazwisko2
interface g0/1
 ip address 10.0.2.1 255.255.255.0
 no shutdown
 exit
interface s0/0/0
 ip address 172.16.3.2 255.255.255.252
 no shutdown
 exit
end
show controllers s0/0/0
```

Tak samo jak na R1: jeżeli jest `DCE`, dodaj `clock rate 64000` na s0/0/0.

### Weryfikacja (1e, 1f, 1g)

1. Na obu routerach wykonaj `show ip interface brief`. Interfejsy muszą mieć stan `up` / `up`.
2. Wykonaj testy i zanotuj wyniki:

| Test | Oczekiwany wynik |
|---|---|
| PC1 `ping 10.0.1.1` | działa |
| PC2 `ping 10.0.2.1` | działa |
| R1 `ping 172.16.3.2` | działa |
| PC1 `ping 10.0.2.254` (PC2) | **nie działa**, bo brak tras |
| PC1 `ping 8.8.8.8` | działa: Loopback należy do R1, a R1 jest bramą PC1 |
| PC2 `ping 8.8.8.8` | **nie działa** |

3. Wykonaj `show ip route` na R1 i R2. Widoczne są tylko wpisy `C` i `L`, czyli sieci podłączone bezpośrednio.

---

## 5. Zadanie 2 — routing statyczny (ocena 3,0)

### R1

```
conf t
ip route 10.0.2.0 255.255.255.0 172.16.3.2
end
```

### R2

```
conf t
ip route 10.0.1.0 255.255.255.0 172.16.3.1
ip route 0.0.0.0 0.0.0.0 172.16.3.1
end
```

Trasa `0.0.0.0` kieruje ruch do „Internetu” przez R1.

### Weryfikacja

- `ping` PC1 ↔ PC2 w obie strony.
- `ping` z każdego PC do każdego interfejsu routerów.
- `ping 8.8.8.8` z obu PC.
- `tracert 10.0.2.254` z PC1 pokazuje trasę przez R1 i R2.
- `show ip route` na R1 i R2: opisz wpisy `S` i `S*` (trasa domyślna, *gateway of last resort*).

---

## 6. Zadanie 3 — RIPv2 (ocena 3,5)

### Krok 1: usuń trasy statyczne

R1:
```
conf t
no ip route 10.0.2.0 255.255.255.0 172.16.3.2
end
```

R2:
```
conf t
no ip route 10.0.1.0 255.255.255.0 172.16.3.1
no ip route 0.0.0.0 0.0.0.0 172.16.3.1
end
show ip route static        ! ma być pusto
```

### Krok 2: R1 — trasa domyślna na Loopback i RIP

```
conf t
ip route 0.0.0.0 0.0.0.0 loopback0
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 network 172.16.0.0
 redistribute static
end
```

- **Nie** dodawaj `network 8.0.0.0`, bo R1 nie może rozgłaszać sieci publicznej.
- `redistribute static` rozgłasza trasę domyślną do R2. Alternatywa: `default-information originate`.

### Krok 3: R2 — RIP

```
conf t
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 network 172.16.0.0
end
```

### Weryfikacja

1. Wykonaj te same pingi co w zadaniu 2. `ping 8.8.8.8` z PC2 **musi** działać.
2. Na R1:
   - `show ip route` pokazuje wpis `R 10.0.2.0` i `S* 0.0.0.0`.
   - `show ip route static` pokazuje **jedną** trasę.
3. Na R2:
   - `show ip route` pokazuje wpisy `R 10.0.1.0` i `R* 0.0.0.0/0`.
   - `show ip route static` jest **pusty**.
4. Wykonaj `show ip protocols`: wersja 2, wpisane sieci, timery 30/180/180/240.

---

## 7. Zadanie 4 — analiza RIP (ocena 4,0)

1. Na PC1 uruchom **Wireshark** i wybierz kartę podłączoną do switcha.
2. Wpisz filtr `rip` i odczekaj 1–2 minuty.
3. Otwórz jeden pakiet i odpowiedz na pytania (porównaj odpowiedzi z przechwyceniem):

| Pytanie | Odpowiedź |
|---|---|
| a) adres źródłowy | interfejs routera, np. `10.0.1.1` (R1 G0/1) |
| a) adres docelowy | `224.0.0.9`, multicast do wszystkich routerów RIPv2 |
| b) warstwa transportowa | UDP, port źródłowy i docelowy **520** |
| c) zawartość | Command: Response, Version 2. Lista tras: sieć, maska, next hop, metryka (liczba skoków, maksymalnie 15) |
| c) częstotliwość | co **30 s** oraz od razu po zmianie topologii (triggered update) |

4. Zrób zrzut ekranu ze szczegółami pakietu oraz kolumną Time, żeby pokazać odstępy około 30 s.

> Uwaga: rozgłaszanie RIP w stronę LAN można wyłączyć poleceniem `passive-interface g0/1`. **Nie** rób tego przed zadaniem 4, bo PC nie przechwyci pakietów RIP.

---

## 8. Zadanie 5 — dodanie R3 (ocena 4,5)

### Okablowanie

| Z | Do | Kabel |
|---|---|---|
| R1 **G0/0** | R3 **G0/0** | **skrosowany** (crossover) |
| R2 **S0/0/1** | R3 **S0/0/1** | szeregowy (sprawdź DCE) |
| PC (dowolny) | R3 **CONSOLE** | konsolowy, możesz przełożyć z R1 albo R2 |

### R1 — nowy interfejs

```
conf t
interface g0/0
 ip address 172.16.4.1 255.255.255.252
 no shutdown
end
```

### R2 — nowy interfejs

```
conf t
interface s0/0/1
 ip address 172.16.5.1 255.255.255.252
 no shutdown
end
show controllers s0/0/1
```

Jeżeli jest `DCE`, dodaj `clock rate 64000` na s0/0/1.

Na R1 i R2 nie zmieniasz RIP, bo `network 172.16.0.0` już obejmuje sieci D i E.

### R3 (wyczyść go tak jak w kroku 2.7)

```
enable
conf t
hostname R3_Nazwisko
no ip domain-lookup
interface g0/0
 ip address 172.16.4.2 255.255.255.252
 no shutdown
 exit
interface s0/0/1
 ip address 172.16.5.2 255.255.255.252
 no shutdown
 exit
interface loopback0
 ip address 192.168.3.1 255.255.255.0
 exit
router rip
 version 2
 no auto-summary
 network 172.16.0.0
 network 192.168.3.0
end
show controllers s0/0/1
```

Jeżeli jest `DCE`, dodaj `clock rate 64000` na s0/0/1.

### Weryfikacja

1. Sprawdź łączność:
   - PC1 `ping 192.168.3.1`
   - PC2 `ping 192.168.3.1`
   - R3 `ping 8.8.8.8`
2. Wykonaj `show ip route` na R1, R2 i R3:
   - R3 ma wpisy `R` do sieci A i B oraz `R*` 0.0.0.0. **Nie ma** wpisów `S`.
   - Wykonaj `show ip route static` na R3: wynik ma być pusty.

---

## 9. Zadanie 6 — symulacja awarii (ocena 5,0)

### Przygotowanie

1. Na **każdym** PC otwórz 3 okna cmd:
   ```
   ping -t 8.8.8.8
   ping -t 192.168.3.1
   ping -t 10.0.2.254      (na PC2: 10.0.1.254)
   ```
2. Zanotuj **TTL** odpowiedzi:
   - Router Cisco odpowiada z TTL startowym 255.
   - Windows odpowiada z TTL startowym 128.
   - Każdy router po drodze zmniejsza TTL o 1.

   | Ping z PC1 do | Trasa | Oczekiwany TTL |
   |---|---|---|
   | 8.8.8.8 | R1 | 255 |
   | 192.168.3.1 | R1 → R3 | 254 |
   | PC2 | R1 → R2 | 126 |

3. Na R1 i R2 (PuTTY) włącz debugowanie:
   ```
   debug ip routing
   ```
   Opcjonalnie dodaj `debug ip rip`.
4. Zanotuj aktualny czas (zegar w Windows albo `show clock`).

### a) Awaria łącza R1–R3

1. Wyjmij kabel z R1 G0/0.
2. Obserwuj:
   - Ile pingów do 192.168.3.1 ma status *Request timed out* i po jakim czasie pingi wracają.
   - Nowy TTL: 253, bo trasa prowadzi teraz przez R2.
   - Debug na R1: usunięta trasa i nowa trasa przez 172.16.3.2.
3. Na R1 wykonaj `show ip route` i zrób zrzut ekranu.

### b) Awaria łącza R1–R2

1. Włóż z powrotem kabel R1–R3. Odczekaj, aż pingi wrócą do TTL 254.
2. Wyjmij kabel szeregowy R1–R2.
3. Obserwuj:
   - Pingi PC1 ↔ PC2 idą teraz przez R3: TTL 125, czyli 128 − 3.
   - Ping PC2 → 8.8.8.8 idzie przez R3.
   - Debug na R1 i R2.
4. Zmierz **czas zbieżności**: od pierwszego *timed out* do pierwszej poprawnej odpowiedzi.
   - Gdy wyjęcie kabla powoduje stan interfejsu `down`, zbieżność trwa kilka sekund (triggered update).
   - Gdy interfejs zostaje `up`, a łącze nie działa, trwa to do 180 s (timer invalid) plus holddown 180 s.
5. Na wszystkich routerach wykonaj `show ip route` i zrób zrzuty ekranu.

### Zakończenie debugowania

```
undebug all
```

Pingi zatrzymasz skrótem `Ctrl+C`.

---

## 10. Sprzątanie (obowiązkowe)

Na **każdym** routerze (R1, R2, R3):

```
enable
erase startup-config
reload
```

- Na pytanie o zapis odpowiedz **no**.
- Potwierdź reload klawiszem **Enter**.

Na PC:
- Przywróć DHCP na karcie sieciowej (*Uzyskaj adres IP automatycznie*).
- Włącz zaporę Windows.
- Odłóż kable na miejsce.

---

## Ściąga: najczęstsze problemy

| Objaw | Przyczyna / rozwiązanie |
|---|---|
| Interfejs serial `up/down` | brak `clock rate` po stronie DCE |
| Interfejs `administratively down` | brak `no shutdown` |
| Ping PC↔PC nie działa, ping do routera działa | zapora Windows albo zła brama na PC |
| `Translating "xyz"...` po literówce | brak `no ip domain-lookup`. Przerwij skrótem `Ctrl+Shift+6` |
| Brak tras `R` | inna wersja RIP po obu stronach albo brakujące `network` |
| Trasy z sumaryzacją (np. 10.0.0.0/8) | brak `no auto-summary` |
| PC2 nie pinguje 8.8.8.8 po RIP | brak `redistribute static` na R1 |
| G0/0 R1–R3 nie wstaje | użyj kabla **skrosowanego** |
