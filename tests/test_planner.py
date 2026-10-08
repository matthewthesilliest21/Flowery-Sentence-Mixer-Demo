import unittest
from voice_mixer.models import Fragment
from voice_mixer.planner import plan_sentence

class TestPlanner(unittest.TestCase):
    def test_phrase_preferred(self):
        fs=[Fragment('phrase',"your dad's",'a.wav',0,.5,.95),Fragment('word','your','b.wav',0,.2,.95),Fragment('word',"dad's",'c.wav',0,.2,.95),Fragment('word','falling','d.wav',0,.4,.95)]
        p=plan_sentence("Your dad's falling!",fs)
        self.assertEqual(p.steps[0].fragment.text,"your dad's")
    def test_possessive_suffix_can_be_reused(self):
        fs=[
          Fragment('word','your','your.wav',0,.2,.95),
          Fragment('word','dad','dad.wav',0,.22,.95,('D','AE','D')),
          Fragment('phone','z','z.wav',0,.12,.95,('Z',)),
          Fragment('word','falling','falling.wav',0,.4,.95,('F','AO','L','IH','NG')),
        ]
        p=plan_sentence("Your dad's falling!",fs)
        self.assertEqual([s.target_text for s in p.steps], ['your','dad',"'s",'falling'])

    def test_missing_not_generated(self):
        p=plan_sentence('banana',[Fragment('word','your','a.wav',0,.2)])
        self.assertIsNone(p.steps[0].fragment)

    def test_safe_uses_word_final_f(self):
        fs=[
          Fragment('phone','S','s.wav',0,.12,.95,('S',),'^','AA'),
          Fragment('phone','EY','ey.wav',0,.12,.95,('EY',),'W','T'),
          Fragment('phone','F','f_onset.wav',0,.12,.95,('F',),'^','AE'),
          Fragment('phone','F','f_final.wav',.2,.32,.95,('F',),'IY','$'),
        ]
        p=plan_sentence('safe',fs)
        self.assertEqual(p.steps[0].reason,'assembled from 3 phonemes')
        self.assertEqual(p.steps[0].audio_fragments[-1].source,'f_final.wav')

if __name__=='__main__': unittest.main()
