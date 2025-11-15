![Screenshot of Window](kid3-tag-copy.png)

# Kid3 Tag Copier

A simple wrapper for copying metadata tags from one audio file to another using Kid3. `kid3-cli` must be available on path.

## Installation

Ensure `kid3-cli` is installed using apt, pacman, dnf, etc.

```shell
# Debian-based (Ubuntu-based)
sudo apt install kid3-cli

# Arch-based
sudo pacman -S kid3
paru -S kid3

# Fedora
sudo dnf install kid3
```

### pipx

Install using `pipx`:

```shell
pipx install git+https://github.com/WhonderWy/kid3-tag-copy.git
```

### AppImage

Download [and `chmod +x`] from Releases.

## Usage

Run without arguments for GUI mode.

```shell
kid3-tag-copy --src A1.mp3 A2.mp3 A3.mp3 C1.mp3 --DST B1.flac B2.flac B3.flac B4.flac
```

|Source|Destination|
|----|----|
| A1 | B1 |
| A2 | B2 |
| A3 | B3 |
| C1 | B4 |

