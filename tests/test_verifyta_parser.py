import unittest

from uppaal_mcp.verifyta import parse_verifyta_outcomes, summarize_status


class VerifytaParserTests(unittest.TestCase):
    def test_parse_satisfied_and_not_satisfied(self) -> None:
        stdout = """
        Verifying formula 1 at /nta/queries/query[1]/formula
        -- Formula is satisfied.
        Verifying formula 2 at /nta/queries/query[2]/formula
        -- Formula is NOT satisfied.
        """
        outcomes = parse_verifyta_outcomes(stdout, ["A[] not deadlock", "E<> Bad"])
        self.assertEqual([item.status for item in outcomes], ["satisfied", "not_satisfied"])
        self.assertEqual(outcomes[0].formula, "A[] not deadlock")
        self.assertEqual(summarize_status(0, outcomes, stdout, ""), "not_satisfied")

    def test_summarize_all_satisfied(self) -> None:
        stdout = "-- Formula is satisfied."
        outcomes = parse_verifyta_outcomes(stdout, ["A[] not deadlock"])
        self.assertEqual(summarize_status(0, outcomes, stdout, ""), "satisfied")

    def test_summarize_error_without_outcomes(self) -> None:
        self.assertEqual(summarize_status(1, [], "", "syntax error"), "error")


if __name__ == "__main__":
    unittest.main()
