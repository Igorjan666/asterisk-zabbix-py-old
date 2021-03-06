# coding=utf-8
import pexpect
from . import settings


class AmiException(Exception):
    pass


class TelnetAmi:
    connect = None
    action_id = 1

    def __init__(self, host, port, username, password):
        self.password = password
        self.username = username
        self.port = port
        self.host = host

    def get_action_id(self):
        return ++self.action_id

    def init(self, command, options, timeout=settings.DEFAULT_TIMEOUT):
        self.connect = pexpect.spawn('telnet %s %s' % (self.host, self.port), timeout=timeout)
        verbosity = options.get("verbosity")
        if verbosity:
            self.connect.logfile = command.stdout
        self.connect.expect("Asterisk Call Manager/%s\r\n" % settings.AMI_VERSION, timeout=timeout)
        self.connect.setecho(False)

    def login(self, timeout=settings.DEFAULT_TIMEOUT):
        self.connect.sendline("Action: Login")
        self.connect.sendline("ActionID: %s" % self.get_action_id())
        self.connect.sendline("Username: %s" % self.username)
        self.connect.sendline("Secret: %s" % self.password)
        self.connect.sendline("")
        self.connect.sendline("")

        self.connect.expect("Authentication accepted\r", timeout=timeout)
        self.connect.sendline("Action: Events")
        self.connect.sendline("EventMask: Off\r")
        self.connect.expect("Events: Off\r", timeout=timeout)

    def logoff(self):
        self.connect.sendline("Action: Logoff\r")

    def execute(self, action, params, callback, check_result=True, timeout=settings.DEFAULT_TIMEOUT):
        self.connect.sendline("Action: %s" % action)
        self.connect.sendline("ActionID: %s" % self.get_action_id())
        for key, value in params.items():
            self.connect.sendline("%s: %s" % (key, value))
        self.connect.sendline()

        if check_result:
            expects = ["Response: Success\r", "Response: Error\r", "Response: Follows\r"]
            status = self.connect.expect(expects, timeout=timeout)
            if status == 1:
                message = "Error AMI"
                self.connect.expect("Message: (.*)\r")
                if self.connect.match:
                    message = self.connect.match.group(1)
                raise AmiException(message)

        return callback(self.connect, timeout)

    def close(self):
        self.connect.close()
