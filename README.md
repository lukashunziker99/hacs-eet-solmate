# EET SolMate — Home Assistant Integration

Native Home Assistant integration for the [EET SolMate](https://www.eet.energy/) PV
storage system. It talks to the SolMate over its WebSocket API — **locally** (recommended)
or via the EET cloud — and exposes live values as sensors plus writable controls.

It is a clean reimplementation of the SolMate protocol used by the official
[`eet-energy/solmate-sdk`](https://github.com/eet-energy/solmate-sdk), but built on Home
Assistant's own aiohttp client (no extra dependency, no separate event loop).

## Features

- **Sensors** generated automatically from `live_values` — typically PV power,
  injection power, battery flow and battery state of charge.
- **Numbers** (read + write): minimum injection (W), maximum injection (W),
  minimum battery (%).
- **Service** `solmate.set_boost` to trigger a temporary injection boost.
- Local *or* cloud connection, automatic reconnect, config via the UI.

## Installation (HACS)

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/lukashunziker99/hacs-eet-solmate`, category **Integration**.
2. Search for **EET SolMate**, download, and **restart** Home Assistant.
3. **Settings → Devices & Services → Add Integration → EET SolMate**.

## Configuration

| Field | Notes |
|-------|-------|
| Serial number | e.g. `X2S1K0506A00000001` |
| User password | your SolMate user password |
| Local IP address | optional — e.g. `192.168.0.138`. Leave **empty** to use the EET cloud. |
| Port | default `9124` (local only) |

Local mode connects to `ws://<IP>:9124/`; cloud mode connects to
`wss://sol.eet.energy:9124`. Local is faster and keeps everything off the cloud.

## Notes

- `battery_state` is scaled to a percentage automatically whether the firmware
  reports a 0–1 fraction or a 0–100 value.
- The current value shown on the number entities is read back from the device
  when possible; otherwise it falls back to the last value you set (restored
  across restarts). If a value reads as *unknown*, check **Diagnostics** for the
  exact key names your firmware uses and adjust `value_keys` in `number.py`.
- To use PV/injection power on the Energy dashboard, wrap them in a Riemann-sum
  (integration) or utility-meter helper to get kWh.

## License

MIT — see [LICENSE](LICENSE).
