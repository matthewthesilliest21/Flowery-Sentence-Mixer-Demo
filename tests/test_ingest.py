import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from voice_mixer.demo import create_demo
from voice_mixer.ingest import save_whisperx_result
from voice_mixer.models import Fragment
from voice_mixer.storage import load_library, save_library
from index_phones_with_mfa import _word_phone_sequence


RESULT = {
    'segments': [{
        'text': 'hello', 'start': 0.0, 'end': 0.5,
        'words': [{'word': 'hello', 'start': 0.0, 'end': 0.5, 'score': 0.9}],
        'chars': [{'char': 'h', 'start': 0.0, 'end': 0.1, 'score': 0.9}],
    }]
}


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.library = self.root / 'data' / f'.codex_test_library_{uuid.uuid4().hex}.json'
        self.source = self.root / 'input_audio' / 'codex_test.wav'

    def tearDown(self):
        if self.library.exists():
            self.library.unlink()

    def test_whisperx_reindex_replaces_existing_fragments(self):
        save_whisperx_result(RESULT, str(self.source), self.library)
        save_whisperx_result(RESULT, str(self.source), self.library)
        fragments = load_library(self.library)
        self.assertEqual([f.kind for f in fragments].count('character'), 1)
        self.assertEqual([f.kind for f in fragments].count('word'), 1)
        self.assertEqual([f.kind for f in fragments].count('phrase'), 1)

    def test_whisperx_refresh_keeps_mfa_word_and_phrase_alignment(self):
        save_library(self.library, [
            Fragment('phone', 'HH', str(self.source), 0, .1, .9, ('HH',), '^', 'EH'),
            Fragment('word', 'reviewed', str(self.source), 0, .5, .95),
            Fragment('phrase', 'reviewed line', str(self.source), 0, .5, .95),
        ])
        save_whisperx_result(RESULT, str(self.source), self.library)
        save_whisperx_result(RESULT, str(self.source), self.library)
        fragments = load_library(self.library)
        self.assertEqual([f.text for f in fragments if f.kind == 'word'], ['reviewed'])
        self.assertEqual([f.text for f in fragments if f.kind == 'phrase'], ['reviewed line'])
        self.assertEqual([f.kind for f in fragments].count('phone'), 1)
        self.assertEqual([f.kind for f in fragments].count('character'), 1)

    def test_demo_does_not_replace_real_library(self):
        with patch('voice_mixer.demo.tone'), patch('voice_mixer.demo.save_library') as save:
            created = create_demo(self.root)
        self.assertEqual(created.name, 'demo_library.json')
        self.assertEqual(save.call_args.args[0], created)

    def test_word_phone_metadata_uses_aligned_variant(self):
        intervals = [
            (0.0, .1, 'W'), (.1, .2, 'IH'), (.2, .3, 'N'), (.3, .4, 'D'),
        ]
        self.assertEqual(_word_phone_sequence(0.0, .4, intervals), ('W', 'IH', 'N', 'D'))


if __name__ == '__main__':
    unittest.main()
