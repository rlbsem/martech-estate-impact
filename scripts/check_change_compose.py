"""Inspect actual exact-project containers or independently establish their removal."""

import argparse
import json
import subprocess

from change_repository import save

PROJECT = "change-assurance-qa"
LABEL = "label=com.docker.compose.project=" + PROJECT


def command(args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--clean", action="store_true")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if args.clean:
        observed = {
            "containers": command(["ps", "-aq", "--filter", LABEL]).splitlines(),
            "volumes": command(["volume", "ls", "-q", "--filter", LABEL]).splitlines(),
            "networks": command(["network", "ls", "-q", "--filter", LABEL]).splitlines(),
        }
        assert not any(observed.values()), "exact project resources remain"
        save(
            args.output,
            dict(
                status="passed",
                exact_project=PROJECT,
                residual_counts={k: len(v) for k, v in observed.items()},
            ),
        )
    else:
        ids = command(["ps", "-aq", "--filter", LABEL]).splitlines()
        checked = []
        for cid in ids:
            obj = json.loads(command(["inspect", cid]))[0]
            service = obj["Config"]["Labels"]["com.docker.compose.service"]
            if service in {"console", "seed"}:
                assert obj["Config"]["User"] == "10001:10001"
                assert obj["HostConfig"]["ReadonlyRootfs"]
                assert "ALL" in obj["HostConfig"]["CapDrop"]
                assert "no-new-privileges:true" in obj["HostConfig"]["SecurityOpt"]
                if service == "console":
                    assert all(m["Destination"] != "/private/admin.json" for m in obj["Mounts"])
                    assert all(not m["RW"] for m in obj["Mounts"])
                    assert obj["HostConfig"]["PortBindings"]["8594/tcp"][0]["HostIp"] == "127.0.0.1"
                else:
                    assert obj["State"]["ExitCode"] == 0 and obj["State"]["Status"] == "exited"
            if service == "postgres":
                assert not obj["HostConfig"]["PortBindings"]
            checked.append(service)
        assert sorted(checked) == ["console", "postgres", "seed"]
        save(
            args.output,
            dict(
                status="passed",
                exact_project=PROJECT,
                services=sorted(checked),
                console_reader_mount_only=True,
                nonroot_readonly_application=True,
                no_database_host_port=True,
            ),
        )
    print(
        "Exact-project container security/teardown checks passed; private inspection payloads omitted."
    )


if __name__ == "__main__":
    main()
