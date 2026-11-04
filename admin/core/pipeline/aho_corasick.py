import os
import ahocorasick
from typing import List, Optional

class SensitiveWordFilter:
    def __init__(self, words_file_path: str):
        self.words_file_path = words_file_path
        self.automaton = ahocorasick.Automaton()
        self.words: List[str] = []
        self.reload()

    def reload(self):
        self.automaton = ahocorasick.Automaton()
        self.words.clear()
        if os.path.exists(self.words_file_path):
            with open(self.words_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w:
                        self.words.append(w)
                        self.automaton.add_word(w, w)
        if self.words:
            self.automaton.make_automaton()

    def contains_sensitive(self, text: str) -> Optional[str]:
        if not self.words:
            return None
        for _, word in self.automaton.iter(text):
            return word
        return None

    def update_words(self, new_words: List[str]):
        os.makedirs(os.path.dirname(self.words_file_path), exist_ok=True)
        with open(self.words_file_path, "w", encoding="utf-8") as f:
            for w in new_words:
                w_clean = w.strip()
                if w_clean:
                    f.write(w_clean + "\n")
        self.reload()
