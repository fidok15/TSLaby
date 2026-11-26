# Monitorowanie wydajności systemu – Raspberry Pi + NetData – ściąga

Sieć labu: 192.168.255.0/24. `yy` = końcówka adresu Twojego RPi.

---

## 0. Połączenie

```bash
ssh root@192.168.255.yy          # hasło: clustering2025
```
Przy pierwszym logowaniu Armbian zada pytania:
- nowe hasło roota – `clustering2025`
- powłoka – `bash`
- nowy użytkownik – `maintenance`, hasło `administration`
- strefa czasowa – `Europe/Warsaw`
- reszta – Enter / domyślne

Dalej najlepiej pracować jako `maintenance` (`ssh maintenance@192.168.255.yy`) – stąd `sudo` w poleceniach.
IP sprawdzisz na RPi przez `ip a` (interfejs `eth0`, linia `inet`).

---

## Część 1 – systemd i instalacja NetData

### 1. Czy NetData jest zainstalowany
```bash
sudo systemctl status netdata          # oczekiwane: Unit netdata.service could not be found.
systemctl list-units | grep netdata    # pusto; bez grep: przewijanie, wyjście "q"
```

### 2. Instalacja
```bash
sudo apt-get update && sudo apt-get install -y netdata
```

### 3. Zależności jednostki
```bash
systemctl list-dependencies netdata
```
Bezpośrednie zależności: `-.mount` (root FS), `system.slice` (cgroup), `tmp.mount`, `sysinit.target`.
- `.mount` – punkt montowania
- `.slice` – grupa jednostek do zarządzania zasobami (cgroups)
- `.target` – punkt synchronizacji (grupa jednostek, "etap" startu systemu)
- `.service` – usługa/proces

### 4. Plik jednostki
```bash
systemctl cat netdata
```
Na co wskazać w sprawozdaniu:
- `[Unit] Description=` – opis; `After=` – kolejność startu
- `[Service] Type=simple` – proces z `ExecStart` jest procesem głównym, systemd uznaje usługę za uruchomioną od razu
- `ExecStart=/usr/sbin/netdata -D` – co jest uruchamiane (`-D` = nie demonizuj się, zostań na pierwszym planie – systemd pilnuje procesu)
- ścieżka pliku w 1. linii: `/usr/lib/systemd/system/netdata.service`

### 5. Status
```bash
systemctl status netdata               # Active: active (running), Loaded: ... enabled
sudo ss -tlnp | grep 19999             # nasłuch: 127.0.0.1:19999
```

### 6. Dostęp z PC
Przeglądarka: `http://192.168.255.yy:19999` → **ERR_CONNECTION_REFUSED** (oczekiwane).
Test lokalny na RPi:
```bash
curl localhost:19999 -s > /dev/null && echo "success"
```
- `curl localhost:19999` – żądanie HTTP do lokalnej usługi na porcie 19999
- `-s` – tryb cichy (bez paska postępu)
- `> /dev/null` – wyrzucenie odpowiedzi HTML
- `&& echo "success"` – wypisz tylko, gdy curl zakończył się kodem 0

### 7. Dostęp z zewnątrz
```bash
sudo nano /etc/netdata/netdata.conf
```
Zmień `bind socket to IP = 127.0.0.1` na `bind socket to IP = 0.0.0.0` (Ctrl+O, Enter, Ctrl+X).
To samo jedną komendą:
```bash
sudo sed -i 's/bind socket to IP = 127.0.0.1/bind socket to IP = 0.0.0.0/' /etc/netdata/netdata.conf
grep "bind socket" /etc/netdata/netdata.conf
```
Restart i weryfikacja:
```bash
sudo systemctl restart netdata
systemctl status netdata               # active (running) since ... "Xs ago" = świeżo przeładowana
sudo ss -tlnp | grep 19999             # teraz 0.0.0.0:19999
```
Przeglądarka na PC: `http://192.168.255.yy:19999` – panel działa.

`0.0.0.0` = nasłuchuj na wszystkich interfejsach. `127.0.0.1` = tylko loopback (dostęp wyłącznie z samego RPi).

---

## Część 2 – testy obciążenia

```bash
sudo apt-get update && sudo apt-get install -y stress
free -h        # ile RAM i swap (Armbian ma zwykle swap na zram)
df -h ~        # ile wolnego miejsca – test dysku zapisuje pliki
nproc          # liczba rdzeni (RPi 4 = 4)
```

W panelu NetData wykresy można szukać po nazwie (np. wpisać `pgfaults`). Zanotuj godzinę startu każdego testu – łatwiej potem znaleźć pik na wykresie i zrobić screenshot. Między testami odczekaj ~1 min, żeby wykresy wróciły do stanu spoczynku.

Opcjonalnie w drugim terminalu SSH: `vmstat 1` (kolumny: `r` kolejka, `si/so` swap, `bi/bo` dysk, `us/sy/wa` CPU).

### Test pamięci
```bash
stress --vm 10 --timeout 60
```
10 procesów, każdy w pętli alokuje 256 MB (domyślne `--vm-bytes`), zapisuje do każdej strony i zwalnia.

| Metryka | Oczekiwane |
|---|---|
| `mem.available` | wyraźny spadek (do ~2,5 GB zajęte) |
| `mem.committed` | skok w górę (Rys. 12) |
| `mem.pgfaults` | duży wzrost minor page faults – każdy dotyk nowej strony = page fault |
| `mem.swap` / `mem.zram_*` | jeśli RAM się kończy – rośnie zużycie swapu (zram) |

Wpływ poza RAM (oczekiwany): **CPU** wysokie, głównie `system` (jądro obsługuje page faulty i alokację), przy zram dodatkowo kompresja = CPU; rośnie `system.load`, `cpu.cpufreq` na max, temperatura. Przy małej pamięci możliwy OOM killer (`dmesg | tail`).

### Test procesora
```bash
stress --cpu 10 --timeout 120
```
10 procesów liczy w pętli `sqrt()` – czysta praca CPU w przestrzeni użytkownika.

| Metryka | Oczekiwane |
|---|---|
| `system.cpu` / `user.cpu_utilization` | ~100%, prawie całość `user` |
| `system.load` | ~10 (10 procesów gotowych do pracy na 4 rdzeniach) |
| `cpu.cpufreq` | skok do max (1,5–1,8 GHz); spadek w trakcie = throttling termiczny |
| `cpu.interrupts` / `system.interrupts` | wzrost – przerwania zegara i IPI (przełączanie 10 procesów na 4 rdzeniach) |
| `cpu.softirqs` | wzrost `SCHED`, `TIMER`, `RCU` – praca planisty |
| `system.ctxt` | więcej przełączeń kontekstu |

Wpływ poza CPU: **temperatura** SoC rośnie (`sensors.*`/`cpu.temperature`) – oczekiwane, więcej pracy = więcej ciepła. Pamięć i dysk praktycznie bez zmian – `sqrt()` nie używa RAM ani I/O, to też oczekiwane. Panel NetData może lekko "przycinać" – sam NetData walczy o CPU.

### Test dysku
Uruchom w katalogu domowym (nie w `/tmp` – na Armbianie to często tmpfs w RAM, wtedy dysk się nie ruszy):
```bash
cd ~
stress --hdd 10 --timeout 120
```
10 procesów w pętli zapisuje plik 1 GB (domyślne `--hdd-bytes`) i go usuwa. Jeśli `df -h ~` pokazuje mało miejsca:
```bash
stress --hdd 4 --hdd-bytes 256M --timeout 120
```

| Metryka | Oczekiwane |
|---|---|
| `disk.ops` | dużo operacji zapisu (writes) |
| `disk.io` | przepustowość zapisu na limicie karty SD / dysku |
| `disk.backlog` | rośnie – żądania czekają w kolejce, nośnik nie nadąża |
| `disk.busy` / `disk.util` | ~100% – dysk zajęty cały czas |
| `disk.await` | rosnący czas obsługi żądania |

Wpływ poza dysk (oczekiwany): **CPU `iowait`** rośnie – procesy czekają na I/O; `system` CPU rośnie (obsługa zapisu w jądrze). **Pamięć**: rośnie page cache, `mem.writeback` i dirty pages – jądro buforuje zapisy w RAM, zanim trafią na nośnik. `system.load` rośnie mimo niskiego użycia CPU – w Linuksie load liczy też procesy w stanie D (czekające na I/O).

---

## Sprzątanie (obowiązkowe)

```bash
sudo sed -i 's/bind socket to IP = 0.0.0.0/bind socket to IP = 127.0.0.1/' /etc/netdata/netdata.conf
sudo systemctl restart netdata
sudo ss -tlnp | grep 19999             # znowu 127.0.0.1:19999
pkill stress                           # gdyby coś zostało
```

---

## Dodatkowe pytania – szkic odpowiedzi

**1. Kiedy takie narzędzie by się przydało (np. C++)?**
Wyciek pamięci w programie C++ – `mem.available` spada liniowo w czasie, aż do OOM. Nieskończona pętla lub busy-waiting zamiast blokującego oczekiwania – 100% jednego rdzenia. Program "zawieszający się" bez obciążenia CPU – wysoki `iowait`/backlog dysku albo czekanie na sieć. Porównanie wydajności dwóch wersji kodu pod tym samym obciążeniem.

**2. Jakie błędy można wychwycić?**
- wycieki pamięci (rosnące zużycie RAM, swap, OOM)
- wycieki deskryptorów plików / gniazd (`apps.files`, `apps.sockets`)
- nadmierna liczba wątków/procesów, fork bomby
- busy-waiting, nieskończone pętle, złe użycie spinlocków (CPU bez sensownej pracy)
- nieefektywne I/O: zapis po bajcie, brak buforowania, zbyt częste `fsync` (dużo ops, mała przepustowość)
- lock contention / deadlocki (spadek przepustowości, dużo przełączeń kontekstu albo zero aktywności)
- wycieki połączeń sieciowych, retransmisje, zbyt wiele połączeń TIME_WAIT

**3. Logowanie metryk w dużej infrastrukturze**
- **5 serwerów** – agent (NetData) na każdym, panele osobno albo NetData Parent/Child (streaming do jednego węzła); proste alerty mailowe.
- **50 serwerów** – centralna baza szeregów czasowych (Prometheus/InfluxDB) + Grafana, agenci/eksportery na hostach, automatyczna konfiguracja (Ansible), wspólne reguły alertów (Alertmanager), centralne logi (Loki/ELK).
- **500 serwerów** – hierarchia/federacja (Prometheus federation, Thanos/Mimir/VictoriaMetrics), service discovery zamiast statycznej listy hostów, retencja i downsampling starych danych, agregacja metryk (nie każdy szczegół z każdego hosta), alerty na poziomie usług (SLO), a nie pojedynczych maszyn, wysoka dostępność samego systemu monitoringu.
