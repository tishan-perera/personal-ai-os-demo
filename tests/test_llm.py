import unittest

from atrium.llm import DemoBrain, HttpBrain, brain_from_env
from atrium.office import Office


class LlmTests(unittest.TestCase):
    def test_demo_brain_is_the_default_even_when_a_key_is_present(self) -> None:
        brain = brain_from_env({"ATRIUM_LLM_API_KEY": "not-a-real-key"})
        self.assertIsInstance(brain, DemoBrain)
        self.assertFalse(brain.enabled)

    def test_switch_without_a_key_stays_on_demo(self) -> None:
        brain = brain_from_env({"ATRIUM_LLM": "on"})
        self.assertIsInstance(brain, DemoBrain)

    def test_switch_and_key_build_the_optional_client(self) -> None:
        brain = brain_from_env(
            {
                "ATRIUM_LLM": "true",
                "ATRIUM_LLM_API_KEY": "not-a-real-key",
                "ATRIUM_LLM_MODEL": "demo-model",
            }
        )
        self.assertIsInstance(brain, HttpBrain)
        self.assertTrue(brain.enabled)
        self.assertEqual(brain.model, "demo-model")

    def test_unreachable_provider_falls_back_to_scripted_text(self) -> None:
        brain = HttpBrain(
            api_key="not-a-real-key",
            base_url="http://127.0.0.1:9",
            model="demo-model",
            timeout=0.3,
        )
        office = Office(brain=brain)
        result = office.handle("How does the November household budget look?")
        self.assertEqual(result["turn"]["mode"], "demo")
        self.assertIn("Ellis Ward", result["turn"]["reply"])
        self.assertIsNone(result["proposal"])


if __name__ == "__main__":
    unittest.main()
