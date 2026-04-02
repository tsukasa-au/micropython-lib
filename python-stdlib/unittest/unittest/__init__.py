import io
import sys

try:
    import ucontextlib as contextlib
except ImportError:
    import contextlib

try:
    import traceback
except ImportError:
    traceback = None


class SkipTest(Exception):
    pass


class AssertRaisesContext:
    def __init__(self, exc):
        self.expected = exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.exception = exc_value
        if exc_type is None:
            assert False, "%r not raised" % self.expected
        if issubclass(exc_type, self.expected):
            # store exception for later retrieval
            self.exception = exc_value
            return True
        return False


class _Outcome:
    def __init__(self, result: TestResult):
        self.result = result
        self.success = True

    @contextlib.contextmanager
    def wrap_execution(self, test_case: tuple[str, ...], is_subtest: bool = False):
        old_success = self.success
        self.success = True
        try:
            yield
        except KeyboardInterrupt as exc:
            # Ensure that tests are interruptable
            raise exc
        except SkipTest as exc:
            self.success = False
            reason: str = exc.args[0]
            self.result.addSkip(test_case, reason)
        except:
            self.success = False
            exc_info = sys.exc_info()
            if is_subtest:
                self.result.addSubTest(test_case, test_case, exc_info)
            else:
                exc_value = exc_info[1]
                assert exc_value is not None
                if isinstance(exc_value, AssertionError):
                    self.result.addFailure(test_case, exc_value)
                else:
                    self.result.addError(test_case, exc_value)
        finally:
            exc_info = None
            self.success = self.success and old_success


class TestCase:
    def __init__(self, methodName="runTest", *, _test_name: tuple[str, ...] = ()):
        self._test_method_name = methodName
        self._test_name = _test_name
        self._outcome: _Outcome | None = None

    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def id(self):
        return f"{self.__class__.__qualname__}.{self._test_method_name}"

    def defaultTestResult(self):
        return TestResult()

    def run(self, result: None | TestResult = None):
        if result is None:
            result = self.defaultTestResult()

        test_function = getattr(self, self._test_method_name)

        result.startTest(self._test_name)
        try:
            self._outcome = _Outcome(result)
            try:
                with self._outcome.wrap_execution(self._test_name):
                    self.setUp()

                if self._outcome.success:
                    with self._outcome.wrap_execution(self._test_name):
                        ret = test_function()
                        if ret is not None:
                            raise ValueError(
                                f"Test functions should return None, instead got {ret!r}."
                            )

                with self._outcome.wrap_execution(self._test_name):
                    self.tearDown()
                self.doCleanups()

                if self._outcome.success:
                    result.addSuccess(self._test_name)
            finally:
                self._outcome = None
        finally:
            result.stopTest(self._test_name)
        return result

    def addCleanup(self, func, *args, **kwargs):
        if not hasattr(self, "_cleanups"):
            self._cleanups = []
        self._cleanups.append((func, args, kwargs))

    def doCleanups(self):
        if hasattr(self, "_cleanups"):
            while self._cleanups:
                func, args, kwargs = self._cleanups.pop()
                func(*args, **kwargs)

    @contextlib.contextmanager
    def subTest(self, msg=None, **params):
        parts = []
        if msg:
            parts.append(msg)
        if params:
            parts.append(", ".join(f"{k}={v}" for k, v in params.items()))
        if not parts:
            parts.append("(<subtest>)")
        subtest_name = self._test_name + tuple(parts)
        with self._outcome.wrap_execution(subtest_name, is_subtest=True):
            yield

    def skipTest(self, reason):
        raise SkipTest(reason)

    def fail(self, msg=""):
        assert False, msg

    def assertEqual(self, x, y, msg=""):
        if not msg:
            msg = "%r vs (expected) %r" % (x, y)
        assert x == y, msg

    def assertNotEqual(self, x, y, msg=""):
        if not msg:
            msg = "%r not expected to be equal %r" % (x, y)
        assert x != y, msg

    def assertLessEqual(self, x, y, msg=None):
        if msg is None:
            msg = "%r is expected to be <= %r" % (x, y)
        assert x <= y, msg

    def assertGreaterEqual(self, x, y, msg=None):
        if msg is None:
            msg = "%r is expected to be >= %r" % (x, y)
        assert x >= y, msg

    def assertAlmostEqual(self, x, y, places=None, msg="", delta=None):
        if x == y:
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if abs(x - y) <= delta:
                return
            if not msg:
                msg = "%r != %r within %r delta" % (x, y, delta)
        else:
            if places is None:
                places = 7
            if round(abs(y - x), places) == 0:
                return
            if not msg:
                msg = "%r != %r within %r places" % (x, y, places)

        assert False, msg

    def assertNotAlmostEqual(self, x, y, places=None, msg="", delta=None):
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if not (x == y) and abs(x - y) > delta:
                return
            if not msg:
                msg = "%r == %r within %r delta" % (x, y, delta)
        else:
            if places is None:
                places = 7
            if not (x == y) and round(abs(y - x), places) != 0:
                return
            if not msg:
                msg = "%r == %r within %r places" % (x, y, places)

        assert False, msg

    def assertIs(self, x, y, msg=""):
        if not msg:
            msg = "%r is not %r" % (x, y)
        assert x is y, msg

    def assertIsNot(self, x, y, msg=""):
        if not msg:
            msg = "%r is %r" % (x, y)
        assert x is not y, msg

    def assertIsNone(self, x, msg=""):
        if not msg:
            msg = "%r is not None" % x
        assert x is None, msg

    def assertIsNotNone(self, x, msg=""):
        if not msg:
            msg = "%r is None" % x
        assert x is not None, msg

    def assertTrue(self, x, msg=""):
        if not msg:
            msg = "Expected %r to be True" % x
        assert x, msg

    def assertFalse(self, x, msg=""):
        if not msg:
            msg = "Expected %r to be False" % x
        assert not x, msg

    def assertIn(self, x, y, msg=""):
        if not msg:
            msg = "Expected %r to be in %r" % (x, y)
        assert x in y, msg

    def assertIsInstance(self, x, y, msg=""):
        assert isinstance(x, y), msg

    def assertRaises(self, exc, func=None, *args, **kwargs):
        if func is None:
            return AssertRaisesContext(exc)
        with AssertRaisesContext(exc):
            func(*args, **kwargs)

    @contextlib.contextmanager
    def assertWarns(self, warn):
        yield


class _SingleFunctionTest(TestCase):
    """Wrapper class to run simple test functions."""

    def __init__(self, *, func, _test_name: tuple[str, ...]):
        super().__init__(methodName="runTest", _test_name=_test_name)
        self._func = func

    def runTest(self):
        return self._func()

    def id(self):
        return " ".join(self._test_name)


def skip(msg):
    def _decor(fun):
        # We just replace original fun with _inner
        def _inner(*args):
            raise SkipTest(msg)

        return _inner

    return _decor


def skipIf(cond, msg):
    if not cond:
        return lambda x: x
    return skip(msg)


def skipUnless(cond, msg):
    if cond:
        return lambda x: x
    return skip(msg)


def expectedFailure(test):
    def test_exp_fail(*args, **kwargs):
        try:
            test(*args, **kwargs)
        except AssertionError:
            # Ignore failure
            pass
        except:
            raise
        else:
            assert False, "unexpected success"

    return test_exp_fail


class TestSuite:
    def __init__(self, name=""):
        self._tests = []
        self.name = name

    def addTest(self, test):
        if isinstance(test, type) and issubclass(test, TestCase):
            raise TypeError("TestCases must be instantiated before calling addTest()", test)
        elif isinstance(test, TestCase):
            pass
        elif not callable(test):
            raise TypeError("Not callable", test)
        else:
            raise NotImplementedError(
                "Directly invoking callables as test methods is not supported"
            )
        self._tests.append(test)

    def run(self, result):
        for c in self._tests:
            if callable(c):
                c(result)
            else:
                c.run(result)
        return result

    def _load_testcase(self, tc: type[TestCase]):
        self._tests.append(_TestCaseTestSuite(self.name, tc))

    def _load_module(self, mod):
        for tn in dir(mod):
            c = getattr(mod, tn)
            if isinstance(c, object) and isinstance(c, type) and issubclass(c, TestCase):
                self._load_testcase(c)
            elif tn.startswith("test") and callable(c):
                self.addTest(_SingleFunctionTest(func=c, _test_name=(tn, f"({self.name})")))


class _TestCaseTestSuite(TestSuite):
    def __init__(self, name: str, test_cls: type[TestCase]):
        super().__init__(name=name)
        self._test_cls = test_cls

    def addTest(self, test):
        raise NotImplementedError

    def run(self, result):
        set_up_class = getattr(self._test_cls, "setUpClass", lambda: None)
        tear_down_class = getattr(self._test_cls, "tearDownClass", lambda: None)

        suite_name = self.name
        try:
            suite_name += f".{self._test_cls.__qualname__}"
        except AttributeError:
            pass
        suite_name = f"({suite_name})"

        test_methods: list[str] = []
        if hasattr(self._test_cls, "runTest"):
            test_methods.append("runTest")
        else:
            for name in dir(self._test_cls):
                if not name.startswith("test"):
                    continue
                m = getattr(self._test_cls, name)
                if not callable(m):
                    continue
                test_methods.append(name)
        test_methods.sort()

        set_up_class()
        try:
            for name in test_methods:
                o = self._test_cls(methodName=name, _test_name=(name, suite_name))
                o.run(result)
        finally:
            tear_down_class()


class TestRunner:
    def run(self, suite: TestSuite):
        res = TestResult()
        suite.run(res)

        res.printErrors()
        print("----------------------------------------------------------------------")
        print("Ran %d tests\n" % res.testsRun)
        if res.failuresNum > 0 or res.errorsNum > 0:
            print("FAILED (failures=%d, errors=%d)" % (res.failuresNum, res.errorsNum))
        else:
            msg = "OK"
            if res.skippedNum > 0:
                msg += " (skipped=%d)" % res.skippedNum
            print(msg)

        return res


TextTestRunner = TestRunner


class TestResult:
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        if stream is None:
            stream = sys.stdout
        self._stream = stream
        self.testsRun: int = 0
        # NOTE: in CPython, errors, failures, and skipped have the type
        # `tuple[TestCase, str]`
        self.errors: list[tuple[tuple[str, ...], str]] = []
        self.failures: list[tuple[tuple[str, ...], str]] = []
        self.skipped: list[tuple[tuple[str, ...], str]] = []
        self._newFailures: int = 0
        self._newErrors: int = 0
        self._newSkipped: int = 0

    def wasSuccessful(self):
        return not bool(self.errors or self.failures)

    def startTest(self, test: tuple[str, ...]):
        print(f"{' '.join(test)} ...", end="", file=self._stream)
        self._newFailures = 0
        self._newErrors = 0
        self._newSkipped = 0
        self.testsRun += 1

    def stopTest(self, test: tuple[str, ...]):
        if self._newErrors:
            print(" ERROR", file=self._stream)
        elif self._newFailures:
            print(" FAIL", file=self._stream)
        elif self._newSkipped:
            pass
        else:
            print(" ok", file=self._stream)

    def addSuccess(self, test: tuple[str, ...]): ...

    def addError(self, test: tuple[str, ...], err: BaseException):
        self.errors.append((test, _capture_exc(err, None)))
        self._newErrors += 1

    def addFailure(self, test: tuple[str, ...], err: BaseException):
        self.failures.append((test, _capture_exc(err, None)))
        self._newFailures += 1

    def addSkip(self, test: tuple[str, ...], reason: str):
        self.skipped.append((test, reason))
        self._newSkipped += 1
        print(" skipped:", reason, file=self._stream)

    def addExpectedFailure(self, test: tuple[str, ...], err: BaseException): ...
    def addUnexpectedSuccess(self, test: tuple[str, ...]): ...

    def addSubTest(
        self,
        test: tuple[str, ...],
        subtest: tuple[str, ...],
        err: tuple[type[BaseException], BaseException, None] | None,
    ):
        if err is None:
            return
        _exc_type, exc_value, _tb = err

        if isinstance(exc_value, SkipTest):
            self.skipped.append((subtest, exc_value.args[0]))
        elif isinstance(exc_value, AssertionError):
            self.failures.append((subtest, _capture_exc(exc_value, None)))
            self._newFailures += 1
        else:
            self.errors.append((subtest, _capture_exc(exc_value, None)))
            self._newErrors += 1

    def printErrors(self):
        if self.errors or self.failures:
            print(file=self._stream)
            self.printErrorList(self.errors)
            self.printErrorList(self.failures)

    def printErrorList(self, lst: list[tuple[tuple[str, ...], str]]):
        sep = "----------------------------------------------------------------------"
        for test, e in lst:
            detail = " ".join(test)
            print(
                "======================================================================",
                file=self._stream,
            )
            print(f"FAIL: {detail}", file=self._stream)
            print(sep, file=self._stream)
            print(e, file=self._stream)

    def __repr__(self):
        # Format is compatible with CPython.
        return "<unittest.result.TestResult run=%d errors=%d failures=%d>" % (
            self.testsRun,
            self.errorsNum,
            self.failuresNum,
        )

    # MicroPython specific
    @property
    def errorsNum(self):  # For compatability with MicroPython < 1.28
        return len(self.errors)

    @property
    def failuresNum(self):  # For compatability with MicroPython < 1.28
        return len(self.failures)

    @property
    def skippedNum(self):  # For compatability with MicroPython < 1.28
        return len(self.skipped)

    def __iadd__(self, other: TestResult):
        self.testsRun += other.testsRun
        self.errors.extend(other.errors)
        self.failures.extend(other.failures)
        self.skipped.extend(other.skipped)
        self._newFailures += other._newFailures
        self._newErrors += other._newErrors
        self._newSkipped += other._newSkipped
        return self


def _capture_exc(exc, exc_traceback):
    buf = io.StringIO()
    if hasattr(sys, "print_exception"):
        sys.print_exception(exc, buf)
    elif traceback is not None:
        traceback.print_exception(None, exc, exc_traceback, file=buf)
    return buf.getvalue()


# This supports either:
#
# >>> import mytest
# >>> unitttest.main(mytest)
#
# >>> unittest.main("mytest")
#
# Or, a script that ends with:
# if __name__ == "__main__":
#     unittest.main()
# e.g. run via `mpremote run mytest.py`
def main(module="__main__", testRunner=None):
    if testRunner is None:
        testRunner = TestRunner()
    elif isinstance(testRunner, type):
        testRunner = testRunner()

    if isinstance(module, str):
        module = __import__(module)
    suite = TestSuite(module.__name__)
    suite._load_module(module)
    result = testRunner.run(suite)
    if not result.wasSuccessful():
        sys.exit(result.failuresNum + result.errorsNum)
    return result
