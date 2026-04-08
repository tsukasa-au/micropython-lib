import unittest


class TestUnittestClassSetup(unittest.TestCase):
    class_setup_var = 0

    @classmethod
    def setUpClass(cls):
        assert cls is TestUnittestClassSetup
        TestUnittestClassSetup.class_setup_var += 1

    @classmethod
    def tearDownClass(cls):
        assert cls is TestUnittestClassSetup
        # Not sure how to actually test this, but we can check (in the test case below)
        # that it hasn't been run already at least.
        TestUnittestClassSetup.class_setup_var = -1

    def testSetUpTearDownClass_1(self):
        assert TestUnittestClassSetup.class_setup_var == 1, TestUnittestClassSetup.class_setup_var

    def testSetUpTearDownClass_2(self):
        # Test this twice, as if setUpClass() gets run like setUp() it would be run twice
        assert TestUnittestClassSetup.class_setup_var == 1, TestUnittestClassSetup.class_setup_var


class TestUnittestSetup(unittest.TestCase):
    per_class_setup_called = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.per_instance_setup_called = 0

    def setUp(self):
        self.per_instance_setup_called += 1
        self.__class__.per_class_setup_called += 1

    def testSetUpTearDown_1(self):
        # Test that setUp
        if self.per_instance_setup_called != 1:
            raise AssertionError(
                "Setup called incorrect number of times", self.per_instance_setup_called
            )
        if self.__class__.per_class_setup_called != 1:
            raise AssertionError(
                "Setup called incorrect number of times", self.__class__.per_class_setup_called
            )

    @unittest.skip(
        "unittest framework incorrectly calls tests on the same instance of TestCase (so __init__ is only called once)"
    )
    def testSetUpTearDown_2(self):
        # Test that setUp
        if self.per_instance_setup_called != 1:
            raise AssertionError(
                "Setup called incorrect number of times", self.per_instance_setup_called
            )
        if self.__class__.per_class_setup_called != 2:
            raise AssertionError(
                "Setup called incorrect number of times", self.__class__.per_class_setup_called
            )


if __name__ == "__main__":
    unittest.main()
