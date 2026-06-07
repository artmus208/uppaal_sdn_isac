import unittest

from uppaal_mcp.examples import EXAMPLE_DESCRIPTIONS, get_builtin_example, list_builtin_examples
from uppaal_mcp.validation import parse_queries_text, validate_model_text


class ValidationTests(unittest.TestCase):
    def test_builtin_examples_are_statically_valid(self) -> None:
        for name in EXAMPLE_DESCRIPTIONS:
            with self.subTest(name=name):
                example = get_builtin_example(name)
                report = validate_model_text(example.model_xml, example.queries)
                self.assertTrue(report.ok, report.errors)
                self.assertGreaterEqual(len(report.templates), 1)
                self.assertGreaterEqual(len(report.queries), 1)

    def test_builtin_examples_expose_phy_category(self) -> None:
        examples = {item["name"]: item for item in list_builtin_examples()}
        self.assertEqual(examples["phy_contract_skeleton"]["category"], "phy")
        self.assertTrue(examples["phy_contract_skeleton"]["is_phy"])
        self.assertEqual(get_builtin_example("phy_contract_skeleton").category, "phy")

    def test_parse_queries_text_ignores_comments_and_blanks(self) -> None:
        formulas = parse_queries_text(
            """
            // comment
            A[] not deadlock

            E<> P.Done
            """
        )
        self.assertEqual(formulas, ["A[] not deadlock", "E<> P.Done"])


if __name__ == "__main__":
    unittest.main()
