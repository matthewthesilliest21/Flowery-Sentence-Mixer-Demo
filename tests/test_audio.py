import unittest
from unittest.mock import patch

from voice_mixer.audio import render_plan
from voice_mixer.models import Fragment
from voice_mixer.planner import plan_sentence


class TestAudioRender(unittest.TestCase):
    def test_incomplete_sentence_is_not_rendered(self):
        plan = plan_sentence('hello banana', [
            Fragment('word', 'hello', 'hello.wav', 0, .3),
        ])
        with patch('voice_mixer.audio.load_fragment') as load_fragment:
            with self.assertRaisesRegex(ValueError, 'missing audio for: banana'):
                render_plan(plan, 'unused.wav')
        load_fragment.assert_not_called()


if __name__ == '__main__':
    unittest.main()
