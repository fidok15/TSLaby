# Temat 2: Konfiguracja małej sieci – ściąga

Wszystkie bloki można wklejać do konsoli (PuTTY / Tera Term, port COM, 9600 8N1).
Wklejaj po jednym bloku – IOS gubi znaki przy długim paste'u. Po każdym bloku zerknij, czy nie ma `% Invalid input`.

Jeśli router ma porty `G0/0/0` zamiast `G0/0` (ISR 4321), podmień nazwy interfejsów.

---

## 0. Start – czyszczenie urządzeń (jeśli ktoś coś zostawił)

R1:
```
enable
erase startup-config
reload
```
S1:
```
enable
erase startup-config
delete flash:vlan.dat
reload
```
Na pytanie `System configuration has been modified. Save?` → `no`. Po restarcie na `Would you like to enter the initial configuration dialog?` → `no`.

---

## 1. Topologia 1 (3,0)

Okablowanie: **PC-A ↔ R1 G0/1**, **R1 G0/0 ↔ S1 (dowolny port, np. F0/1)**, **PC-B ↔ S1 (np. F0/6)**.

### R1
```
enable
configure terminal
hostname R1
no ip domain-lookup
security passwords min-length 10
enable secret cisco12345
line console 0
 password ciscoconpass
 login
 exec-timeout 5 0
 logging synchronous
 exit
line vty 0 4
 password ciscovtypass
 login
 transport input telnet
 exec-timeout 5 0
 logging synchronous
 exit
service password-encryption
interface g0/0
 ip address 192.168.0.1 255.255.255.0
 no shutdown
 exit
interface g0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
 exit
end
copy running-config startup-config
```

### S1
```
enable
configure terminal
hostname S1
no ip domain-lookup
enable secret cisco12345
line vty 0 15
 password ciscovtypass
 login
 transport input telnet
 exit
interface vlan 1
 ip address 192.168.0.2 255.255.255.0
 no shutdown
 exit
ip default-gateway 192.168.0.1
end
copy running-config startup-config
```
`enable secret` na S1 jest potrzebny – bez niego po telnecie `enable` zwróci `% No password set`.
`ip default-gateway` jest potrzebny, żeby S1 odpowiadał na ping z PC-A (inna podsieć).

### PC (Windows, cmd jako administrator)
```
netsh interface ip set address "Ethernet" static 192.168.1.10 255.255.255.0 192.168.1.1   :: PC-A
netsh interface ip set address "Ethernet" static 192.168.0.10 255.255.255.0 192.168.0.1   :: PC-B
netsh advfirewall set allprofiles state off                                                :: inaczej Windows nie odpowiada na ping
```
Nazwę karty sprawdź przez `netsh interface show interface`. Można też ustawić w GUI (ncpa.cpl).

### Weryfikacja
```
PC-A> ping 192.168.0.10        (PC-B)
PC-A> ping 192.168.0.2         (S1)
PC-A> telnet 192.168.1.1       (R1, hasło ciscovtypass, potem enable → cisco12345)
PC-A> telnet 192.168.0.2       (S1)
R1# show ip interface brief
R1# show running-config        (hasła jako "7 xxxx" po service password-encryption)
S1# show ip interface brief
```
Brak polecenia `telnet` w Windows → `dism /online /Enable-Feature /FeatureName:TelnetClient` albo PuTTY (typ połączenia Telnet).

---

## 2. SSH na R1 (3,5)

```
configure terminal
ip domain-name CCNA-lab.com
username admin secret admin1pass
crypto key generate rsa general-keys modulus 1024
ip ssh version 2
line vty 0 4
 transport input ssh
 login local
 exit
end
copy running-config startup-config
```

Weryfikacja:
```
R1# show ip ssh
R1# show ssh            (w trakcie aktywnej sesji)
PC-A> ssh admin@192.168.1.1
```
Jeśli nowy klient OpenSSH odrzuca stary IOS (`no matching key exchange method` / `no matching host key type`):
```
ssh -oKexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oCiphers=+aes128-cbc admin@192.168.1.1
```
albo PuTTY. Telnet do R1 od teraz nie działa – to oczekiwane.

---

## 3. Topologia 2 + DHCPv4 na S1 (4,0)

Przepięcie: **PC-A odpinasz od R1 i wpinasz do S1** (np. F0/11). R1 G0/0 ↔ S1 bez zmian, PC-B ↔ S1 bez zmian.

### R1
```
configure terminal
interface g0/1
 no ip address
 shutdown
 exit
interface loopback 0
 ip address 10.10.10.1 255.255.255.0
 exit
end
copy running-config startup-config
```

### S1
```
configure terminal
ip dhcp excluded-address 192.168.0.1 192.168.0.10
ip dhcp pool DHCP1
 network 192.168.0.0 255.255.255.0
 default-router 192.168.0.1
 dns-server 8.8.8.8
 exit
end
copy running-config startup-config
```
Jeśli S1 nie zna `ip dhcp pool` (obraz IOS bez serwera DHCP) – te same polecenia działają na R1.

### PC-A i PC-B
```
netsh interface ip set address "Ethernet" dhcp
ipconfig /release
ipconfig /renew
ipconfig /all
```
Oczekiwane: adresy od 192.168.0.11 wzwyż, brama 192.168.0.1, DNS 8.8.8.8.

### Weryfikacja
```
S1# show ip dhcp pool
S1# show ip dhcp binding
PC-A> ping 10.10.10.1
```

---

## 4. IPv6 + SLAAC (4,5)

### R1
```
configure terminal
ipv6 unicast-routing
interface g0/0
 ipv6 address 2001:db8:acad:a::1/64
 ipv6 address fe80::1 link-local
 exit
interface loopback 0
 ipv6 address 2001:db8:acad:b::1/64
 ipv6 address fe80::1 link-local
 exit
end
copy running-config startup-config
```
`ipv6 unicast-routing` sprawia, że R1 zaczyna wysyłać Router Advertisement – na tej podstawie PC same budują adres (SLAAC).

### Wireshark (zrób to ZANIM PC dostaną adres albo wymuś ponownie)
1. Na PC-A uruchom Wireshark na karcie Ethernet, filtr: `icmpv6`
2. Wymuś ponowną konfigurację karty:
   ```
   netsh interface set interface "Ethernet" disable
   netsh interface set interface "Ethernet" enable
   ```
3. Szukaj w przechwyceniu:
   - **Router Solicitation (type 133)** – PC → `ff02::2` (wszystkie routery): "jest tu jakiś router?"
   - **Router Advertisement (type 134)** – `fe80::1` → `ff02::1` (wszystkie węzły): prefix `2001:db8:acad:a::/64`, flaga **A=1** (autonomiczna konfiguracja), **M=0, O=0** (bez DHCPv6) → czysty SLAAC
   - **Neighbor Solicitation (type 135)** z adresu `::` → `ff02::1:ffXX:XXXX` – **DAD** (Duplicate Address Detection), PC sprawdza, czy wygenerowany adres jest wolny
   - Brak odpowiedzi na DAD = adres wolny, PC go używa. Brama domyślna = adres źródłowy RA (`fe80::1`).

   Dokładniejszy filtr: `icmpv6.type >= 133 && icmpv6.type <= 136`

### Weryfikacja
```
R1# show ipv6 interface brief
R1# show ipv6 route
R1# show ipv6 neighbors
PC> ipconfig                                    (adres 2001:db8:acad:a:..., brama fe80::1%NN)
PC-A> ping <adres IPv6 PC-B z ipconfig>
PC-A> ping fe80::1%NN                           (NN = numer interfejsu, widoczny w ipconfig po "%")
PC-B> ping 2001:db8:acad:b::1                   (Lo0)
```
Windows domyślnie generuje losowy identyfikator interfejsu (privacy extensions), a nie EUI-64 z MAC – stąd "dziwne" adresy, w tym "Temporary IPv6 Address".

---

## 5. Dostęp do Internetu – NAT (5,0)

Podłącz **R1 G0/1** do gniazda sieci laboratoryjnej.

```
configure terminal
interface g0/1
 ip address dhcp
 no shutdown
 ip nat outside
 exit
interface g0/0
 ip nat inside
 exit
access-list 100 permit ip 192.168.0.0 0.0.0.255 any
ip nat inside source list 100 interface g0/1 overload
end
copy running-config startup-config
```

Sprawdź, czy G0/1 dostał adres i czy jest trasa domyślna:
```
R1# show ip interface brief
R1# show ip route              (szukaj S* 0.0.0.0/0 – IOS dodaje ją z DHCP sam)
```
Jeśli brak `S* 0.0.0.0/0`:
```
R1(config)# ip route 0.0.0.0 0.0.0.0 <brama z sieci labu>
```

### Weryfikacja
```
PC-A> ping <adres G0/1>
PC-A> ping 8.8.8.8
PC-A> nslookup google.com
(przeglądarka na PC-A i PC-B)
R1# show ip nat translations
R1# show ip nat statistics
R1# show ip route
```

---

## 6. Sprzątanie (obowiązkowe)

R1:
```
erase startup-config
reload
```
S1:
```
erase startup-config
delete flash:vlan.dat
reload
```
Na PC: `netsh advfirewall set allprofiles state on` i karta z powrotem na DHCP.

---

## Odpowiedzi na pytania z instrukcji

- **`exec-timeout 5 0`** – wylogowanie sesji po 5 min 0 s bezczynności (składnia: `exec-timeout <minuty> <sekundy>`; `0 0` = nigdy). Chroni przed pozostawieniem otwartej, zalogowanej konsoli.
- **`logging synchronous`** – komunikaty systemowe (np. `%LINK-3-UPDOWN`) nie przerywają wpisywanego polecenia; IOS przepisuje linię z wpisanym tekstem pod komunikatem.
- **`service password-encryption`** – szyfruje hasła zapisane jawnie (console, vty) słabym algorytmem typu 7 – chroni tylko przed podglądnięciem przez ramię, łatwo odwracalne. `enable secret` jest i tak haszowane (typ 5/8/9).
- **`security passwords min-length 10`** – IOS odrzuci krótsze hasła (`% Password too short`). Wszystkie hasła z instrukcji mają ≥10 znaków.
- **`no ip domain-lookup`** – literówka w trybie EXEC nie jest traktowana jako nazwa hosta do rozwiązania przez DNS (brak ~30 s zawieszenia).
- **Przeładowanie bez `copy run start`** – konfiguracja żyje tylko w RAM (running-config); po restarcie router ładuje startup-config z NVRAM, więc wszystkie zmiany przepadają (router wraca do stanu z ostatniego zapisu / pustej konfiguracji).
- **Dlaczego SSH zamiast telnetu** – telnet przesyła wszystko (w tym hasła) jawnym tekstem; SSH szyfruje sesję. `login local` = logowanie z lokalnej bazy użytkowników (`username ...`). Klucz RSA jest potrzebny do zestawienia szyfrowanego kanału; SSHv2 wymaga klucza ≥768 bitów.
- **DHCP – excluded-address** – adresy .1–.10 zarezerwowane dla urządzeń statycznych (R1 .1, S1 .2), serwer ich nie rozda. Proces DORA: Discover → Offer → Request → Ack.
- **SLAAC** – opis wyżej przy Wireshark. Adres = prefiks /64 z RA + 64-bitowy identyfikator interfejsu (EUI-64 lub losowy).
- **Po co NAT** – sieć 192.168.0.0/24 jest prywatna (RFC 1918), routery w Internecie/labie nie mają do niej trasy. PAT (`overload`) podmienia adres źródłowy na adres G0/1 i rozróżnia sesje po numerach portów, więc wiele hostów wychodzi przez jeden adres. ACL 100 określa, które adresy podlegają translacji.
