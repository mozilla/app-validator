from functools import wraps

from nose.tools import eq_

from js_helper import TestCase


def uses_feature(name):
    def wrap(func):
        @wraps(func)
        def inner(self, *args, **kw):
            func(self, *args, **kw)
            self.assert_has_feature(name)
        return inner
    return wrap


class FeatureTester(TestCase):
    def assert_has_feature(self, name):
        assert name in self.err.feature_profile, (
            '"%s" not found in feature profile (%s)' % (
                name, ', '.join(self.err.feature_profile)))


class TestWindowFeatures(FeatureTester):
    """Tests for feature APIs in the global context."""

    @uses_feature("ACTIVITY")
    def test_ACTIVITY(self):
        self.run_script("""
        var x = new MozActivity();
        """)
    
    @uses_feature("LIGHT_EVENTS")
    def test_LIGHT_EVENTS(self):
        self.run_script("""
        window.ondevicelight = function() {};
        """)
    
    @uses_feature("ARCHIVE")
    def test_ARCHIVE(self):
        self.run_script("""
        var x = new ArchiveReader();
        """)
    
    @uses_feature("INDEXEDDB")
    def test_INDEXEDDB(self):
        self.run_script("""
        var x = new mozIndexedDB();
        """)
    
    @uses_feature("PROXIMITY")
    def test_PROXIMITY(self):
        self.run_script("""
        window.ondeviceproximity = function() {};
        """)
    
    @uses_feature("ORIENTATION")
    def test_ORIENTATION(self):
        self.run_script("""
        window.ondeviceorientation = function() {};
        """)
    
    @uses_feature("TOUCH")
    def test_TOUCH(self):
        self.run_script("""
        window.ontouchstart = function() {};
        """)
    
    @uses_feature("AUDIO")
    def test_AUDIO(self):
        self.run_script("""
        var audio = new Audio();
        audio.src = 'asdf';
        """)
    
    @uses_feature("WEBAUDIO")
    def test_WEBAUDIO(self):
        self.run_script("""
        var x = new mozAudioContext();
        """)
    
    @uses_feature("QUOTA")
    def test_QUOTA(self):
        self.run_script("""
        var x = new mozPersistentStorage();
        """)
    
    @uses_feature("QUOTA")
    def test_QUOTA_StorageInfo(self):
        self.run_script("""
        var x = new StorageInfo();
        """)


class TestNavigatorFeatures(FeatureTester):
    """Tests for feature APIs in the navigator.* object."""

    @uses_feature("APPS")
    def test_APPS(self):
        self.run_script("""
        navigator.mozApps.install('foo/bar.webapp');
        """)

    @uses_feature("APPS")
    def test_APPS_not_moz(self):
        self.run_script("""
        navigator.apps.install('foo/bar.webapp');
        """)

    @uses_feature("PACKAGED_APPS")
    def test_PACKAGED(self):
        self.run_script("""
        navigator.apps.installPackage('foo/bar.webapp');
        """)

    @uses_feature("PAY")
    def test_PAY(self):
        self.run_script("""
        navigator.mozPay.foo();
        """)

    @uses_feature("BATTERY")
    def test_BATTERY(self):
        self.run_script("""
        navigator.battery.foo();
        """)

    @uses_feature("BLUETOOTH")
    def test_BLUETOOTH(self):
        self.run_script("""
        navigator.bluetooth.foo();
        """)

    @uses_feature("CONTACTS")
    def test_CONTACTS(self):
        self.run_script("""
        navigator.mozContacts.foo();
        """)

    @uses_feature("DEVICE_STORAGE")
    def test_DEVICE_STORAGE(self):
        self.run_script("""
        navigator.getDeviceStorage();
        """)

    @uses_feature("GEOLOCATION")
    def test_GEOLOCATION(self):
        self.run_script("""
        navigator.getCurrentPosition();
        """)

    @uses_feature("IDLE")
    def test_IDLE(self):
        self.run_script("""
        navigator.addIdleObserver();
        """)

    @uses_feature("NETWORK_INFO")
    def test_NETWORK_INFO(self):
        self.run_script("""
        navigator.connection.foo();
        """)

    @uses_feature("NETWORK_STATS")
    def test_NETWORK_STATS(self):
        self.run_script("""
        navigator.networkStats.foo();
        """)

    @uses_feature("PUSH")
    def test_PUSH(self):
        self.run_script("""
        navigator.mozPush.foo();
        """)

    @uses_feature("TIME_CLOCK")
    def test_TIME_CLOCK(self):
        self.run_script("""
        navigator.mozTime.foo();
        """)

    @uses_feature("VIBRATE")
    def test_VIBRATE(self):
        self.run_script("""
        navigator.vibrate.foo();
        """)

    @uses_feature("FM")
    def test_FM(self):
        self.run_script("""
        navigator.mozFM();
        """)

    @uses_feature("FM")
    def test_FM_FMRadio(self):
        self.run_script("""
        navigator.mozFMRadio();
        """)

    @uses_feature("SMS")
    def test_SMS(self):
        self.run_script("""
        navigator.mozSms.foo();
        """)

    @uses_feature("GAMEPAD")
    def test_GAMEPAD(self):
        self.run_script("""
        navigator.getGamepad();
        """)


class TestInstMembersFeatures(FeatureTester):
    """Tests for feature APIs in instance properties."""

    @uses_feature("TOUCH")
    def test_TOUCH(self):
        self.run_script("""
        document.getElementById('foo').ontouchstart = function() {};
        """)

    @uses_feature("FULLSCREEN")
    def test_FULLSCREEN(self):
        self.run_script("""
        document.getElementById('foo').requestFullScreen();
        """)
