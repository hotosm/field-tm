# Docker organization

This section explains how the Docker deployment works when running `docker-compose`. It gives an overview of what happens when the scripts in `Dockerfile` are run and what happens for each container.

When running `docker-compose`, it sets up the environment for the project and deploys the containers specified in the `docker-compose.yml` file. The scripts in the `Dockerfile` are used to set up the environment and dependencies for each container.

### For example, let's say that we have the following `docker-compose.yml` file

    version: "3"
    services:
    db:
        image: postgres:latest
        environment:
        POSTGRES_USER: user
        POSTGRES_PASSWORD: password
    api:
        build:
        context: .
        dockerfile: Dockerfile
        environment:
        DATABASE_URL: postgresql://user:password@db:5432/mydb
        ports:
        - "8000:8000"
    web:
        build:
        context: .
        dockerfile: Dockerfile
        environment:
        API_URL: http://api:8000
        ports:
        - "3000:3000"

In this file, we have three containers: `db`, `api`, and `web`. For each container, we specify the `image` or `build` to use, any environment variables to set, and any ports to expose.

When we run `docker-compose up`, the scripts in the `Dockerfile` will be run for each container, setting up the environment and dependencies needed for the container to run. Then, for each container, the environment variables will be set, the execute command will be run, and the container will be deployed at the given port.

> Note: this Docker deployment automatically sets up a traefik server with ssh.

# When updating docker

This section explains what to do when updating Docker. It's important to make sure that all the necessary files are updated, including `.prod` and `.local` `docker-compose` or `Dockerfiles`.

For example, if we update the `Dockerfile` to include a new package that our application needs, we need to make sure that we also update the `.prod` and `.local` files as needed. Otherwise, our production deployment may be missing the necessary dependencies, causing our application to fail.

# Debugging when using docker

This section explains how to debug an application when using Docker. It gives an example of how to open a TTY to a container and add a debug line in code using IPython debugger (ipdb).

When we are developing an application, we may encounter bugs that we need to debug. Docker can make this process a bit more complicated, as we need to access the running container to debug our code.

To open a TTY to a container, we can use the following command:

    docker attach <container_name>

For example, if we want to open a TTY to the `fmtm-web-1` container, we would run:

    docker attach fmtm-web-1

Once we have a TTY open, we can add a debug line in our code using IPython debugger (ipdb). This allows us to pause our code at a specific point and interactively debug it using IPython commands.

For example, let's say that we have the following Python code:

    def add_numbers(a, b):
        import ipdb; ipdb.set_trace()
        return a + b

When we call the add_numbers function, our code will pause at the import ipdb; ipdb.set_trace() line, and we can use IPython commands to inspect variables

When this line is reached in the code then the attached tty window will
become interactive with ipdb.

A few of those commands:
[Command CheatSheet](https://wangchuan.github.io/coding/2017/07/12/ipdb-cheat-sheet.html)

- `help`: displays the list of available IPython commands
- `h(elp) <command>`: displays help for the specified command
- `w(here)`: shows the current position in the code
- `d(own)`: moves down one level in the call stack
- `u(p)`: moves up one level in the call stack
- `b(reak) <location> [condition]`: sets a breakpoint at the specified - location, with an optional condition
- `tbreak <location> [condition]`: sets a temporary breakpoint at the - specified location, with an optional condition
- `cl(ear) [bpnumber]`: clears the specified breakpoint, or all breakpoints if no number is given
- `disable <bpnumber> [<bpnumber> ...]`: disables the specified breakpoint(s)
- `enable <bpnumber> [<bpnumber> ...]`: enables the specified breakpoint(s)
- `ignore <bpnumber> <count>`: sets the number of times to ignore the specified breakpoint
- `condition <bpnumber> <condition>`: sets a new condition for the specified breakpoint
- `s(tep)`: steps to the next line of code
- `n(ext)`: executes the next line of code, without stepping into functions
- `unt(il)`: runs the code until it reaches a line with a greater number than the current line
- `r(eturn)`: runs the code until it returns from the current function
- `run [args ...]`: starts the program with the specified arguments
- `c(ont(inue))`: continues running the program until the next breakpoint or until it finishes
- `l(ist) [<first> [<last>]]`: displays the source code around the current position, with an optional range of lines to show
- `a(rgs)`: shows the arguments of the current function
- `p <expression>`: evaluates the expression and prints its value

To exit IPython debugging mode, we can press CTRL + D.

### Conclusion

Overall, the documentation provides a clear overview of how the Docker deployment works when running `docker-compose`, what to do when updating Docker, and how to debug an application when using Docker using IPython debugger (ipdb). The provided examples make it easier to understand how to implement these concepts in practice.
