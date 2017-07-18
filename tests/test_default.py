from pytest import fixture
import yaml


with open("tests/test.yml", "r") as s:
    y = yaml.safe_load(s)

grafana_admin_user = y[0]["vars"]["grafana_admin_user"]
grafana_admin_password = y[0]["vars"]["grafana_admin_password"]


# Adapted from
# http://www.axelspringerideas.de/blog/index.php/2016/08/16/continuously-delivering-infrastructure-part-1-ansible-molecule-and-testinfra/
@fixture()
def Repository_exists(Command):
    """
    Tests if YUM Repo with specific Name exists and is enabled:
    - **repo** - repo name to look for
    **returns** - True if String is found
    """
    def f(repo):
        return (repo in Command.check_output("yum repolist"))
    return f


def test_grafana_repo_is_installed(Repository_exists):
    assert Repository_exists("Grafana upstream yum repo")


def test_grafana_package_is_installed(Package):
    pkg = Package("grafana")
    assert pkg.is_installed


def test_grafana_service_is_enabled(Service):
    svc = Service("grafana-server")
    assert svc.is_enabled


def test_gedash_js_is_installed(File):
    assert File("/usr/share/grafana/public/dashboards/getdash.js").exists


def test_grafana_api_accepts_our_password(Command, TestinfraBackend):
    hostname = TestinfraBackend.get_hostname()
    url = "%s:%s@%s:3000/api/org" % (grafana_admin_user, grafana_admin_password, hostname)
    # This is the simplest one-liner I could find to GET a url and return just
    # the status code.
    # http://superuser.com/questions/590099/can-i-make-curl-fail-with-an-exitcode-different-than-0-if-the-http-status-code-i
    cmd = Command("curl --silent --output /dev/stderr --write-out '%%{http_code}' %s" % url)
    # Expect a 2xx status code.
    assert cmd.stdout.startswith("2")


def test_grafana_has_datasources(Command, TestinfraBackend):
    hostname = TestinfraBackend.get_hostname()
    url = "%s:%s@%s:3000/api/datasources" % (grafana_admin_user, grafana_admin_password, hostname)
    cmd = Command("curl --silent %s" % url)
    assert '"name":"Prometheus"' in cmd.stdout
    assert '"name":"Prometheus2"' in cmd.stdout
    assert '"name":"Influxdb"' in cmd.stdout


def test_grafana_has_users(Command, TestinfraBackend):
    hostname = TestinfraBackend.get_hostname()
    url = "%s:%s@%s:3000/api/users" % (grafana_admin_user, grafana_admin_password, hostname)
    cmd = Command("curl --silent %s" % url)
    assert '"login":"admin"' in cmd.stdout
    assert '"login":"john"' in cmd.stdout
    assert '"login":"peter"' in cmd.stdout


def test_grafana_has_dashboard(Command, TestinfraBackend):
    hostname = TestinfraBackend.get_hostname()
    url = "%s:%s@%s:3000/api/dashboards/db/docker-dashboard" % (grafana_admin_user, grafana_admin_password, hostname)
    cmd = Command("curl --silent %s" % url)
    assert '"slug":"docker-dashboard"' in cmd.stdout
    url = "%s:%s@%s:3000/api/dashboards/db/node-exporter-single-server" % (grafana_admin_user,
                                                                           grafana_admin_password, hostname)
    cmd = Command("curl --silent %s" % url)
    assert '"slug":"node-exporter-single-server"' in cmd.stdout
