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
    def test_all(self):
        def _test(feature, script):
            self.setUp()
            self.setup_err()
            self.run_script(script)
            self.assert_has_feature(feature)

        for feature, script in self.TESTS:
            yield _test, feature, script


class TestWindowFeatures(FeatureTester):
    """Tests for feature APIs in the global context."""

    TESTS = [
        ("ACTIVITY", "var x = new MozActivity();"),
        ("LIGHT_EVENTS", "window.ondevicelight = function() {};"),
        ("ARCHIVE", "var x = new ArchiveReader();"),
        ("INDEXEDDB", "var x = new mozIndexedDB();"),
        ("PROXIMITY", "window.ondeviceproximity = function() {};"),
        ("ORIENTATION", "window.ondeviceorientation = function() {};"),
        ("TOUCH", "window.ontouchstart = function() {};"),
        ("AUDIO", "var audio = new Audio(); audio.src = 'asdf';"),
        ("WEBAUDIO", "var x = new mozAudioContext();"),
        ("QUOTA", "var x = new mozPersistentStorage();"),
        ("QUOTA", "var x = new StorageInfo();"),
        ("WEBRTC_MEDIA", "var x = new MediaStream();"),
        ("WEBRTC_DATA", "var x = new DataChannel();"),
        ("WEBRTC_PEER", "var x = new RTCPeerConnection();"),
        ("SPEECH_SYN", "var x = speechSynthesis.foo();"),
        ("SPEECH_REC", "var x = new SpeechRecognition();"),
        ("POINTER_LOCK", "document.documentElement.requestPointerLock()"),
        ("UDPSOCKET", "var x = new UDPSocket()"),
    ]


class TestNavigatorFeatures(FeatureTester):
    """Tests for feature APIs in the navigator.* object."""

    TESTS = [
        ("APPS", "navigator.mozApps.install('foo/bar.webapp');"),
        ("APPS", "navigator.apps.install('foo/bar.webapp');"),
        ("PACKAGED_APPS", "navigator.apps.installPackage('foo/bar.webapp');"),
        ("PAY", "navigator.mozPay.foo();"),
        ("BATTERY", "navigator.battery.foo();"),
        ("BLUETOOTH", "navigator.bluetooth.foo();"),
        ("CONTACTS", "navigator.mozContacts.foo();"),
        ("DEVICE_STORAGE", "navigator.getDeviceStorage();"),
        ("GEOLOCATION", "navigator.getCurrentPosition();"),
        ("IDLE", "navigator.addIdleObserver();"),
        ("NETWORK_INFO", "navigator.connection.foo();"),
        ("NETWORK_STATS", "navigator.networkStats.foo();"),
        ("PUSH", "navigator.mozPush.foo();"),
        ("TIME_CLOCK", "navigator.mozTime.foo();"),
        ("VIBRATE", "navigator.vibrate.foo();"),
        ("FM", "navigator.mozFM();"),
        ("FM", "navigator.mozFMRadio();"),
        ("SMS", "navigator.mozSms.foo();"),
        ("GAMEPAD", "navigator.getGamepad();"),
        ("MOBILEID", "navigator.getMobileIdAssertion();"),
        ("NOTIFICATION", "navigator.mozNotification.foo();"),
        ("ALARM", "navigator.mozAlarms.foo();"),
        ("TCPSOCKET", "var x = new navigator.mozTCPSocket();"),
        ("THIRDPARTY_KEYBOARD_SUPPORT",
         "var x = navigator.mozInputMethod.foo()"),
        ("NETWORK_INFO_MULTIPLE",
         "var x = navigator.mozMobileConnections.foo();"),
    ]


class TestInstMembersFeatures(FeatureTester):
    """Tests for feature APIs in instance properties."""

    TESTS = [
        ("TOUCH",
            "document.getElementById('foo').ontouchstart = function() {};"),
        ("FULLSCREEN",
            "document.getElementById('foo').requestFullScreen();"),
    ]


class TestGUMFeatures(FeatureTester):
    """Tests for getUserMedia-related feature APIs."""

    TESTS = [
        ("CAMERA", "navigator.getUserMedia({video:true})"),
        ("CAMERA", "navigator.getUserMedia({picture:true})"),
        ("MIC", "navigator.getUserMedia({audio:true})"),
        ("SCREEN_CAPTURE",
            "navigator.getUserMedia({video:{mandatory:"
            "{chromeMediaSource:'screen'}}})"),
    ]
