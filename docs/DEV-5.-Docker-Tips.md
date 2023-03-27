# Docker organization

When `docker-compose` is run:

- the scripts in `Dockerfile` run (there is also a `Dockerfile.prod` for production)
- for each container (`db`,`api`,`web`, etc.):
  - environmental variables are set (the `environment` section of each container)
  - the `execute` command of each container is run
  - the container is deployed at the given `port`

> Note: this Docker deployment automatically sets up a traefik server with ssh.

# When updating docker

Make sure to also update `.prod` and `.local` docker-compose or Dockerfiles as needed!!

# Debugging when using docker

Open tty to container

    docker attach fmtm-web-1

Add debug line in code

    import ipdb;ipdb.set_trace()

When this line is reached in the code then the attached tty window will
become interactive with ipdb.

A few of those commands:
[Command CheatSheet](https://wangchuan.github.io/coding/2017/07/12/ipdb-cheat-sheet.html)

    h(elp)
    w(here)
    d(own)
    u(p)
    b(reak): \[ ([filename:]lineno | function) [, condition] ]
    tbreak: \[ ([filename:]lineno | function) [, condition] ]
    cl(ear): \[bpnumber [bpnumber ...] ]
    disable bpnumber: [bpnumber ...]
    enable bpnumber: [bpnumber ...]
    ignore bpnumber count
    condition bpnumber condition
    s(tep)
    n(ext)
    unt(il)
    r(eturn)
    run [args ...]
    c(ont(inue))
    l(ist): \[first [,last]]
    a(rgs)
    p expression

Debugging commands

    help

To get out of debugging

    CTRL + D
