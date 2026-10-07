<p align="center">
  <a href="https://github.com/lupaxa-security-toolbox">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/security-toolbox/readme-logo.png" alt="Security Toolbox" />
  </a>
</p>

<h1 align="center">IPinfo Update</h1>

Download the IPinfo Lite database for local TCP wrappers and other tools.
The PyPI name is `lupaxa-ipinfo-update`. The console script is
`ipinfo-update`.

The command line overrides the environment. Omit `--token` to use
`IPINFO_TOKEN`, and omit `--output` to use `IPINFO_DATABASE` when that
variable is set. A failed download leaves the previous database in place.

## Install

```bash
pip install lupaxa-ipinfo-update
ipinfo-update --help
```

Requires Python 3.10 or newer. You can also run
`python -m lupaxa.ipinfo_update`.

## CLI

```bash
export IPINFO_TOKEN=your-token
ipinfo-update
ipinfo-update --token your-token --quiet
```

The default path is `/var/lib/ipinfo/ipinfo_lite.mmdb`.
`IPINFO_DATABASE` replaces that default. `--output` replaces both.
If the directory does not exist, it is created. The finished file is mode `0644`.

### Flags

| Flag        | Default                                | Description                                              |
| :---------- | :------------------------------------- | :------------------------------------------------------- |
| `--token`   | `IPINFO_TOKEN`                         | IPinfo access token (`-t`)                               |
| `--output`  | `/var/lib/ipinfo/ipinfo_lite.mmdb`     | Database path (`-o`). `IPINFO_DATABASE` is the fallback  |
| `--timeout` | `60`                                   | HTTP timeout in seconds                                  |
| `--quiet`   | off                                    | Print nothing on success (`-q`)                          |
| `--version` | —                                      | Print the package version and exit                       |

`--token` and `--output` are optional. When `--output` is omitted,
`IPINFO_DATABASE` is used if that variable is set.

### Exit Codes

| Code | When                                                  |
| :--- | :---------------------------------------------------- |
| `0`  | Help, version, or the database was replaced           |
| `1`  | The token is missing, or the download or write failed |
| `2`  | Invalid arguments                                     |

## Cron

```cron
15 3 * * * IPINFO_TOKEN=your-token ipinfo-update --quiet
```

`--quiet` prints nothing when the update succeeds. Failures still go to
stderr and exit `1`, and the previous file is left unchanged.

## Development

```bash
make init
make install-dev
make check
```

<a href="https://github.com/the-lupaxa-project">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
