import unittest
from bladegame.render import Renderer


class UITextLayoutTests(unittest.TestCase):
    def renderer(self):
        r=Renderer.__new__(Renderer)
        r.text_width=lambda text,size,display=False:len(text)
        return r

    def test_korean_words_wrap_without_losing_effect_details(self):
        r=self.renderer();wrap=r.wrap_text
        self.assertEqual(wrap('패링마다 체력 +7',20,6),['패링마다','체력 +7'])

    def test_long_unspaced_label_wraps_at_character_boundaries(self):
        r=self.renderer();wrap=r.wrap_text
        self.assertEqual(wrap('가나다라마바사',20,3),['가나다','라마바','사'])

    def test_existing_short_effect_does_not_gain_blank_lines(self):
        r=self.renderer();wrap=r.wrap_text
        self.assertEqual(wrap('체력 +7',20,20),['체력 +7'])


if __name__=='__main__':unittest.main()
