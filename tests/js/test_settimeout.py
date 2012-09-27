from js_helper import TestCase


class TestSetTimeout(TestCase):

    def do_run(self, script, fails):
        self.setUp()
        self.run_script(script)
        if fails:
            self.assert_failed()
        else:
            self.assert_silent()

    def test_failures(self):
        yield self.do_run, 'setTimeout("abc.def()", 1000);', True
        yield (self.do_run, 'window["set" + "Timeout"]("abc.def()", 1000);',
               True)
        yield self.do_run, 'var x = "foo.bar()";setTimeout(x, 1000);', True
        yield (self.do_run,
               'var x = "foo.bar()";window["set" + "Timeout"](x, 1000);', True)

    def test_successes(self):
        yield self.do_run, 'setTimeout(function(){foo.bar();}, 1000);', False
        yield (self.do_run,
               'window["set" + "Timeout"](function(){foo.bar();}, 1000);',
               False)
        yield self.do_run, 'setTimeout();', False
        yield self.do_run, 'window["set" + "Timeout"]();', False
