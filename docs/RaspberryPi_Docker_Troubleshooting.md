# Raspberry Pi Docker + GitLab Runner Troubleshooting

## 1. Confirmed environment

Current HIL-PI environment:

- Kernel: `aarch64`
- Host package architecture: `armhf`
- Host userspace: 32-bit
- Docker-reported daemon architecture: `aarch64`
- Docker daemon executable: 32-bit ARM/EABI5
- Selected `python:3.11-slim-bookworm` image: `linux/arm/v7`
- Container package architecture: `armhf`
- Container Python pointer size: 32-bit

This is internally consistent. `uname -m` and `platform.machine()` report the
shared host kernel architecture, so they must not be used alone to determine
the container ABI.

Use:

```bash
docker image inspect python:3.11-slim-bookworm \
  --format 'OS={{.Os}} ARCH={{.Architecture}} VARIANT={{.Variant}}'

docker run --rm python:3.11-slim-bookworm sh -lc '
  uname -m
  dpkg --print-architecture
  getconf LONG_BIT
  python -c "import struct; print(struct.calcsize(\"P\") * 8)"
'
```

Expected:

- image: `arm/v7`
- dpkg: `armhf`
- LONG_BIT: `32`
- Python pointer size: `32`

## 2. Why `docker ps --filter name=gitlab-runner` is empty

The runner is installed as a host `systemd` service, not as a Docker container.

```bash
systemctl status gitlab-runner --no-pager
sudo gitlab-runner list
sudo gitlab-runner verify
```

The runner manager calls the host Docker daemon and creates short-lived job
containers. Observe a pipeline with:

```bash
sudo journalctl -u gitlab-runner -f
```

In another terminal:

```bash
watch -n 1 'docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
```

## 3. Docker Engine support limitation

Docker Engine 28 is the last major version supporting Raspberry Pi OS 32-bit
`armhf`. Keep Docker CE and Docker CLI on major version 28 during this project.

```bash
docker version
sudo apt-mark hold docker-ce docker-ce-cli
apt-mark showhold
```

Plan a later migration to 64-bit Raspberry Pi OS.

## 4. Package version installation failures

```bash
uname -m
dpkg --print-architecture
getconf LONG_BIT
apt-cache madison docker-ce | head -20
```

Use the full APT version string, including the epoch prefix such as `5:`.

```bash
VERSION_STRING="$(
  apt-cache madison docker-ce |
  awk '$3 ~ /^5:28\./ {print $3; exit}'
)"

printf 'VERSION_STRING=%s\n' "$VERSION_STRING"
```

Install:

```bash
sudo apt-get install -y \
  docker-ce="$VERSION_STRING" \
  docker-ce-cli="$VERSION_STRING" \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

## 5. Docker daemon does not start

```bash
sudo systemctl status docker --no-pager
sudo journalctl -u docker -n 200 --no-pager
sudo systemctl restart containerd
sudo systemctl restart docker
```

Check storage:

```bash
df -h /
df -i /
docker system df
```

Validate daemon JSON:

```bash
sudo test -f /etc/docker/daemon.json &&
sudo python3 -m json.tool /etc/docker/daemon.json
```

## 6. Permission denied on Docker socket

Symptoms:

- permission denied connecting to `/var/run/docker.sock`
- Docker executor cannot create containers

Fix:

```bash
sudo usermod -aG docker "$USER"
sudo usermod -aG docker gitlab-runner
sudo reboot
```

After reconnecting:

```bash
id -nG
id gitlab-runner
ls -l /var/run/docker.sock
sudo -u gitlab-runner docker version
```

The Docker group grants high host privilege. Use it only on a dedicated test
bench.

## 7. Architecture appears inconsistent

Do not use `uname -m` alone.

```bash
docker image inspect IMAGE \
  --format 'OS={{.Os}} ARCH={{.Architecture}} VARIANT={{.Variant}}'

docker run --rm IMAGE sh -lc '
  uname -m
  dpkg --print-architecture
  getconf LONG_BIT
'
```

Python bitness:

```bash
docker run --rm IMAGE python -c \
'import platform, struct; print(platform.machine(), struct.calcsize("P") * 8)'
```

The current valid combination is:

- kernel/machine: `aarch64`
- package architecture: `armhf`
- Python bits: `32`

## 8. `file: not found`

`python:*slim*` images omit many utilities. This is not an architecture error.
Use `docker/Dockerfile.rpi-qa`, which installs `file`, `git`, `jq`,
`can-utils`, pytest, pyserial, and python-can.

## 9. `no matching manifest for linux/arm/v7`

The image does not provide an ARMv7 variant.

```bash
docker buildx imagetools inspect IMAGE
```

Use an image that includes `linux/arm/v7`.

## 10. `exec format error`

Likely causes:

- AMD64-only executable in an ARM image
- ARM64-only image or executable in the 32-bit ARMv7 environment
- host binaries mounted into a container with a different ABI

Check:

```bash
docker image inspect IMAGE \
  --format '{{.Os}}/{{.Architecture}}/{{.Variant}}'
file /path/to/executable
```

Do not mount host `/usr/bin`, Python, or toolchain binaries into the container.

## 11. GitLab job remains Pending

```bash
sudo gitlab-runner list
sudo gitlab-runner verify
sudo systemctl status gitlab-runner --no-pager
```

A runner must contain every tag listed on the job.

Recommended Docker runner tags:

- `rpi-docker`
- `armhf`
- `armv7`
- `python-test`

Recommended hardware Shell runner tags:

- `rpi-shell`
- `hil`
- `bench-01`
- `stm32f429`
- `stlink`

## 12. Job starts on the wrong runner

Print runner identity in every infrastructure and HIL job:

```yaml
script:
  - echo "runner=$CI_RUNNER_DESCRIPTION"
  - echo "runner_id=$CI_RUNNER_ID"
  - echo "runner_tags=$CI_RUNNER_TAGS"
  - echo "host=$(hostname)"
```

Disable **Run untagged jobs** for dedicated Raspberry Pi runners.

## 13. GitLab helper image failure

A successful manual `docker run` does not prove the complete Docker executor
workflow. GitLab also uses a helper image for clone, cache, and artifact steps.
Inspect failures in:

- Preparing environment
- Getting source from Git repository
- Uploading artifacts

Do not manually set `helper_image` during initial setup.

```bash
sudo journalctl -u gitlab-runner -n 300 --no-pager
sudo sed -n '1,240p' /etc/gitlab-runner/config.toml
```

Do not publish the runner token.

## 14. Custom image does not exist in GitLab Registry

The first build is a bootstrap operation:

1. Run `build_rpi_qa_image` manually on the HIL-PI Shell Runner.
2. Check GitLab **Deploy → Container Registry**.
3. Run `verify_rpi_qa_image`.

The build job uses built-in variables:

- `CI_REGISTRY`
- `CI_REGISTRY_USER`
- `CI_REGISTRY_PASSWORD`

A PAT is not required for the same project registry.

## 15. Docker build location

The DEV-PC only writes and pushes files. Docker build must run on a machine
with Docker:

- manually on HIL-PI after pulling the QA repository, or
- through `build_rpi_qa_image` on the HIL-PI Shell Runner.

The final `.` in `docker build ... .` is the repository-root build context.

## 16. HIL test cannot find ST-Link

```bash
lsusb
openocd --version
id gitlab-runner
```

Install:

```bash
sudo apt-get update
sudo apt-get install -y openocd python3 python3-pytest
```

Add permissions:

```bash
sudo usermod -aG plugdev gitlab-runner

sudo tee /etc/udev/rules.d/60-beog-stlink.rules > /dev/null <<'RULE'
SUBSYSTEM=="usb", ATTR{idVendor}=="0483", MODE="0660", GROUP="plugdev"
RULE

sudo udevadm control --reload-rules
sudo udevadm trigger
sudo systemctl restart gitlab-runner
```

Disconnect and reconnect ST-Link.

## 17. LED test scope and limits

The OpenOCD test verifies:

- ST-Link and target debug connection
- GPIOB clock and registers
- PB0/PB7/PB14 output transitions
- automated JUnit generation

It does not prove visible light output. Attach a photo or video to Jira. It also
does not verify EVSE FreeRTOS, CAN, relay, or safety logic because the CPU is
temporarily halted and GPIO is controlled by the debugger.

Run the LED job manually with external circuits disconnected or confirmed safe.
