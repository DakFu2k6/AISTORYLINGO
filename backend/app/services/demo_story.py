from ai_engine.schemas import FirstChapter, NextChapter, VocabularyItem

DEMO_VOCABULARY = [
    VocabularyItem(
        word="celestial", pronunciation="/səˈles.tʃəl/", part_of_speech="adjective",
        meaning="Relating to the sky or outer space.",
        meaning_vi="Thuộc về bầu trời hoặc vũ trụ.",
        example="The celestial map showed every star.",
    ),
    VocabularyItem(
        word="curious", pronunciation="/ˈkjʊə.ri.əs/", part_of_speech="adjective",
        meaning="Wanting to learn or know something.",
        meaning_vi="Tò mò, muốn tìm hiểu.",
        example="The curious child opened the old box.",
    ),
    VocabularyItem(
        word="portal", pronunciation="/ˈpɔː.təl/", part_of_speech="noun",
        meaning="A large door or gate, often a magical way into another place.",
        meaning_vi="Cánh cổng, lối vào (thường là cổng thần kỳ).",
        example="A glowing portal appeared in the forest.",
    ),
    VocabularyItem(
        word="hesitate", pronunciation="/ˈhez.ɪ.teɪt/", part_of_speech="verb",
        meaning="To wait before doing something because you are not sure.",
        meaning_vi="Do dự, ngập ngừng.",
        example="Do not hesitate to ask for help.",
    ),
    VocabularyItem(
        word="constellation", pronunciation="/ˌkɒn.stəˈleɪ.ʃən/", part_of_speech="noun",
        meaning="A group of stars that forms a pattern in the sky.",
        meaning_vi="Chòm sao.",
        example="Orion is a famous constellation.",
    ),
    VocabularyItem(
        word="guardian", pronunciation="/ˈɡɑː.di.ən/", part_of_speech="noun",
        meaning="A person or being who protects something.",
        meaning_vi="Người bảo vệ, người canh giữ.",
        example="The guardian watched the gate all night.",
    ),
    VocabularyItem(
        word="nebula", pronunciation="/ˈneb.jʊ.lə/", part_of_speech="noun",
        meaning="A cloud of gas and dust in space.",
        meaning_vi="Tinh vân.",
        example="A bright nebula glowed in the telescope.",
    ),
    VocabularyItem(
        word="aurora", pronunciation="/ɔːˈrɔː.rə/", part_of_speech="noun",
        meaning="Colored lights that sometimes appear in the night sky.",
        meaning_vi="Cực quang.",
        example="We watched the aurora from the mountain.",
    ),
]

FIRST_CHAPTER_TEXT = (
    "High above the clouds, where the stars hum ancient melodies, there is a celestial library "
    "made entirely of light. One evening, a curious astronomer named Liora finds a glowing portal "
    "in her observatory. She does not hesitate for long. She steps through and floats among the "
    "stars, where a single constellation spells out words in a language she has never heard. "
    "A guardian made of stardust drifts toward her. Behind it, a soft nebula glows like a sleeping "
    "cloud, and an aurora of green and violet light rolls across the ceiling. "
    "\"Welcome, seeker,\" the guardian says. \"You may read one story, but you must leave one of "
    "your own behind.\""
)

FIRST_CHOICES = [
    "Tell the guardian a story from your childhood",
    "Ask the guardian who built the library",
    "Walk deeper into the glowing library",
]

MIDDLE_CHOICES = [
    "Open the glowing book",
    "Thank the guardian and go home",
    "Follow the aurora to the highest shelf",
]


def demo_first_chapter(target_words: int) -> FirstChapter:
    return FirstChapter(
        title="The Celestial Library",
        content=FIRST_CHAPTER_TEXT,
        choices=FIRST_CHOICES,
        vocabulary=DEMO_VOCABULARY[:target_words],
    )


def demo_next_chapter(choice: str, chapter_number: int, total_chapters: int) -> NextChapter:
    if chapter_number >= total_chapters:
        text = (
            f"Because you chose to \"{choice}\", the library gives you a gift: a single page that "
            "rewrites itself every night. The guardian bows, and the portal opens one last time. "
            "When you step home, the portal closes behind you, but the celestial words still shimmer "
            "in your hands. You smile. The library will always remember you. The End."
        )
        return NextChapter(content=text, choices=[])

    text = (
        f"You decide: \"{choice}\". The guardian smiles, and the nebula above you glows even brighter. "
        "A new aurora ripples through the library, and the curious books on the shelves turn their "
        "pages by themselves. Somewhere in the distance, a constellation begins to move, as if it "
        "wants to show you the way."
    )
    return NextChapter(content=text, choices=MIDDLE_CHOICES)
