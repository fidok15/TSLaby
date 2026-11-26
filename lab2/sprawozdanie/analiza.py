"""Liczy ruch dla kazdej uslugi z plikow pcapng (tshark) i rysuje wykresy natezenia ruchu."""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "wykresy"
OUT.mkdir(exist_ok=True)

CLAUDE = "160.79.104.10"  # ruch Claude Code dzialajacego w tle, nie nalezy do zadnej uslugi
WEB = "(tcp.port in {80, 443} || udp.port == 443)"

USLUGI = {
    "www": ("www/www.pcapng", "10.182.42.126",
            f"{WEB} && !(ip.addr == {CLAUDE})"),
    "poczta": ("mail/poczta.pcapng", "10.182.42.126",
               f"{WEB} && !(ip.addr in {{{CLAUDE}, 142.251.154.5}})"),  # bez meet.google.com
    "radio": ("radio/radio.pcapng", "10.182.42.126",
              "ip.addr == 107.155.103.139"),  # 25443.live.streamtheworld.com - strumien Radia ZET
    "radio_strona": ("radio/radio.pcapng", "10.182.42.126",
                     f"{WEB} && !(ip.addr == {CLAUDE})"),
    "discord": ("discord/discord.pcapng", "10.182.42.126",
                "ip.addr == 162.159.0.0/16 || ip.addr == 104.29.148.109"),
    "discord_glos": ("discord/discord.pcapng", "10.182.42.126",
                     "udp.port == 19315"),
    "ftp_down": ("ftp/ftp.pcapng", "10.23.41.207", "ip.addr == 193.219.28.2"),
    "ftp_up": ("ftp/ftp.pcapng", "10.23.41.207", "ip.addr == 44.241.66.173"),
    "meet": ("googlemeets/google meets.pcapng", "10.23.41.207",
             "udp.port in {3478, 19302..19309} || ip.addr == 74.125.250.0/24 || ip.addr == 142.250.82.0/24"),
    "backup": ("backup/backup.pcapng", "10.23.41.207",
               "ip.addr in {172.66.0.218, 162.159.140.220}"),  # speed.cloudflare.com
}


def licz(nazwa, plik, moje_ip, filtr):
    cmd = ["tshark", "-r", str(ROOT / plik), "-Y", filtr,
           "-T", "fields", "-e", "frame.time_relative", "-e", "frame.len", "-e", "ip.src"]
    wynik = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    down = up = 0
    pk_down = pk_up = 0
    t_min, t_max = float("inf"), 0.0
    sek_down, sek_up = defaultdict(int), defaultdict(int)
    for linia in wynik.splitlines():
        t, dl, src = linia.split("\t")
        t, dl = float(t), int(dl)
        t_min, t_max = min(t_min, t), max(t_max, t)
        if src == moje_ip:
            up += dl; pk_up += 1; sek_up[int(t)] += dl
        else:
            down += dl; pk_down += 1; sek_down[int(t)] += dl
    # czas sesji = caly plik, bo usluga byla uzywana przez caly czas przechwytywania
    czas = float(subprocess.run(["capinfos", "-u", "-M", str(ROOT / plik)], capture_output=True,
                                text=True, check=True).stdout.split(":")[-1].split()[0])
    r = {"plik": plik, "filtr": f"ip.addr == {moje_ip} && ({filtr})", "czas_s": round(czas, 1),
         "down_B": down, "up_B": up, "pk_down": pk_down, "pk_up": pk_up,
         "down_kbps": round(down * 8 / czas / 1000, 1), "up_kbps": round(up * 8 / czas / 1000, 1),
         "max_down_kbps": round(max(sek_down.values(), default=0) * 8 / 1000, 1),
         "max_up_kbps": round(max(sek_up.values(), default=0) * 8 / 1000, 1)}
    if nazwa.startswith(("ftp", "meet", "backup")):  # liczy sie czas faktycznego transferu / rozmowy
        r["czas_transferu_s"] = round(t_max - t_min, 1)
        r["down_kbps_transfer"] = round(down * 8 / r["czas_transferu_s"] / 1000, 1)
        r["up_kbps_transfer"] = round(up * 8 / r["czas_transferu_s"] / 1000, 1)
    n = int(czas) + 1
    xs = list(range(n))
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(xs, [sek_down[i] * 8 / 1e6 for i in xs], lw=0.8, label="pobierane (do stacji)")
    ax.plot(xs, [sek_up[i] * 8 / 1e6 for i in xs], lw=0.8, label="wysyłane (ze stacji)")
    ax.set_xlabel("czas [s]"); ax.set_ylabel("natężenie [Mb/s]")
    ax.set_xlim(0, n); ax.grid(alpha=0.3); ax.legend(loc="upper right")
    fig.tight_layout(); fig.savefig(OUT / f"{nazwa}.pdf"); plt.close(fig)
    return r


if __name__ == "__main__":
    wybrane = sys.argv[1:] or list(USLUGI)
    wyniki = {n: licz(n, *USLUGI[n]) for n in wybrane}
    for n, r in wyniki.items():
        print(n, r)
    (Path(__file__).parent / "wyniki.json").write_text(json.dumps(wyniki, indent=2, ensure_ascii=False))
