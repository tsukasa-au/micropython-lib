import unittest
import helpers


class Basics(helpers.BaseTestCase):
    def test_bare_function__passes(self):
        class FakeModule:
            @staticmethod
            def test_func1(): ...
            @staticmethod
            def test_func2(): ...

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=0)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(
            output,
            f"test_func1 ({self.full_test_name()}) ... ok\ntest_func2 ({self.full_test_name()}) ... ok\n",
        )

    def test_bare_function__fail(self):
        class FakeModule:
            @staticmethod
            def test_func_fail():
                assert False

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(output, f"test_func_fail ({self.full_test_name()}) ... FAIL\n")

    def test_bare_function__error(self):
        class FakeModule:
            @staticmethod
            def test_func_error():
                raise ValueError

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(output, f"test_func_error ({self.full_test_name()}) ... ERROR\n")

    def test_bare_function__expect_failure__fail(self):
        class FakeModule:
            @unittest.expectedFailure
            def test_func_fail():
                assert False

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=0)
        self.assertTrue(result.wasSuccessful())
        # FIXME: This should be "test_func_fail", but the existing
        # implementation pulls the wrong name
        self.assertEqual(output, f"test_exp_fail ({self.full_test_name()}) ... ok\n")

    @unittest.skip("expectedFailure incorrectly consumes all failure types")
    def test_bare_function__expect_failure__error(self):
        class FakeModule:
            @unittest.expectedFailure
            def test_func_error():
                raise ValueError

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(output, f"test_func_error ({self.full_test_name()}) ... ERROR\n")

    @unittest.skip("expectedFailure incorrectly consumes the SkipTest exception")
    def test_bare_function__expect_failure__skip(self):
        class FakeModule:
            @unittest.expectedFailure
            @unittest.skip("reason1")
            def test_func_error():
                raise ValueError

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=1)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(
            output, f"test_func_error ({self.full_test_name()}) ... skipped: reason1\n"
        )

    @unittest.skip("expectedFailure incorrectly consumes the SkipTest exception")
    def test_testcase__expect_failure__skip(self):
        class FakeModule:
            class Test(unittest.TestCase):
                @unittest.expectedFailure
                def test_func_skip_in_test(self):
                    self.skipTest("reason1")

                @unittest.expectedFailure
                @unittest.skip("reason2")
                def test_func_skip_wrap_test(self):
                    pass

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=2)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(
            output,
            f"test_func_skip_in_test ({self.full_test_name()}.Test) ... skipped: reason1\n"
            f"test_func_skip_wrap_test ({self.full_test_name()}.Test) ... skipped: reason2\n",
        )


class TestTestCase(helpers.BaseTestCase):
    def test_method_called__passes(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test1(self): ...
                def test2(self): ...

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=0)
        self.assertEqual(
            output,
            f"test1 ({self.full_test_name()}.Test) ... ok\n"
            f"test2 ({self.full_test_name()}.Test) ... ok\n",
        )

    def test_method_called__fail(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test1(self):
                    self.fail("reason1")

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertEqual(output, f"test1 ({self.full_test_name()}.Test) ... FAIL\n")

    def test_method_called__error(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test1(self):
                    raise ValueError("reason1")

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertEqual(output, f"test1 ({self.full_test_name()}.Test) ... ERROR\n")

    @unittest.skip("unittest framework incorrectly calls `Test.test3`")
    def test_only_calls_methods(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test1(self): ...

                test_copy = test1

                test2 = None

                @property
                def test3(self):
                    raise ValueError

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=0)
        self.assertEqual(
            output,
            f"test1 ({self.full_test_name()}.Test) ... ok\n"
            f"test_copy ({self.full_test_name()}.Test) ... ok\n",
        )

    def test_prefers_runTest(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test1(self):
                    self.fail("wrong method called")

                def runTest(self):
                    pass

                def __repr__(self):
                    # FIXME: Remove this method, it should not be needed
                    return "runTest"

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=0)
        self.assertEqual(output, f"runTest ({self.full_test_name()}.Test) ... ok\n")

    def test_setup_teardown_are_called(self):
        class FakeModule:
            class Test(unittest.TestCase):
                setup_called_times = 0
                teardown_called_times = 0

                def setUp(self):
                    self.__class__.setup_called_times += 1

                def tearDown(self):
                    self.__class__.teardown_called_times += 1

                def test1(self): ...
                def test2(self): ...
                def test3(self):
                    self.fail("failure1")

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertEqual(FakeModule.Test.setup_called_times, 3)
        self.assertEqual(FakeModule.Test.teardown_called_times, 3)
        self.assertTestResult(result, testsRun=3, numFailures=1, numErrors=0, numSkipped=0)
        self.assertEqual(
            output,
            f"test1 ({self.full_test_name()}.Test) ... ok\n"
            f"test2 ({self.full_test_name()}.Test) ... ok\n"
            f"test3 ({self.full_test_name()}.Test) ... FAIL\n",
        )

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_setup__failure_skips_test(self):
        class FakeModule:
            class Test(unittest.TestCase):
                teardown_called_times = 0
                test_called_times = 0

                def setUp(self):
                    raise AssertionError("setUp")

                def tearDown(self):
                    self.__class__.teardown_called_times += 1

                def test(self):
                    self.__class__.test_called_times += 1

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertEqual(FakeModule.Test.teardown_called_times, 1)
        self.assertEqual(FakeModule.Test.test_called_times, 0)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... FAIL\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_setup__errors_skips_test(self):
        class FakeModule:
            class Test(unittest.TestCase):
                teardown_called_times = 0
                test_called_times = 0

                def setUp(self):
                    raise ValueError("setUp")

                def tearDown(self):
                    self.__class__.teardown_called_times += 1

                def test(self):
                    self.__class__.test_called_times += 1

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertEqual(FakeModule.Test.teardown_called_times, 1)
        self.assertEqual(FakeModule.Test.test_called_times, 0)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... ERROR\n")

    def test_setup__explict_skip__skips_test(self):
        class FakeModule:
            class Test(unittest.TestCase):
                teardown_called_times = 0
                test_called_times = 0

                def setUp(self):
                    self.skipTest("reason1")

                def tearDown(self):
                    self.__class__.teardown_called_times += 1

                def test(self):
                    self.__class__.test_called_times += 1

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=1)
        self.assertEqual(FakeModule.Test.teardown_called_times, 1)
        self.assertEqual(FakeModule.Test.test_called_times, 0)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... skipped: reason1\n")

    def test_keyboard_interrupt_not_captured(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def test(self):
                    raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            helpers.run_tests_in_module(self, FakeModule)

    @unittest.skip("unittest framework does not call `TestCase.run` method")
    def test_run_method_overridable(self):
        class FakeModule:
            class Test(unittest.TestCase):
                def run(self, result: unittest.TestResult | None = None):
                    if result is None:
                        result = self.defaultTestResult()

                    tmp_result = unittest.TestResult(stream=result._stream)
                    super().run(tmp_result)
                    if tmp_result.failures:
                        test, err_msg = tmp_result.failures[-1]
                        err_msg += "\nSome extra debugging info"
                        tmp_result.failures[-1] = test, err_msg
                    result += tmp_result
                    return result

                def test1(self):
                    self.fail("reason1")

        result, output = helpers.run_tests_in_module(self, FakeModule)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertEqual(output, f"test1 ({self.full_test_name()}.Test) ... FAIL\n")
        self.assertIn("\nSome extra debugging info", result.failures[-1][1])


if __name__ == "__main__":
    unittest.main()
