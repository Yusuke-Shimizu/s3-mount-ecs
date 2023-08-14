import invoke
import logging

logger = logging.getLogger(__name__)
fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)


@invoke.task
def env(c):
    invoke.run("python3 -m venv .venv")
    print("source .venv/bin/activate.fish")


@invoke.task
def install(c):
    invoke.run("pip install -r requirements.txt -r requirements-dev.txt")


@invoke.task
def uninstall(c):
    invoke.run("pip uninstall -r requirements.txt -r requirements-dev.txt")


@invoke.task
def diff(c):
    invoke.run("cdk diff", pty=True,)


@invoke.task
def deploy(c):
    invoke.run("cdk deploy --require-approval never", pty=True,)

@invoke.task
def destroy(c):
    invoke.run("cdk destroy --force", pty=True,)

@invoke.task
def prune(c):
    invoke.run("df -h | grep /dev/nvm", pty=True,)
    invoke.run("docker system prune -a -f", pty=True,)
    invoke.run("df -h | grep /dev/nvm", pty=True,)

