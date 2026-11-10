"""
Seed The Archives with a full year of rich, long-form diary entries written in the
voice of Raghavan — a 70-year-old retired maths teacher living with early memory loss.

Span: 10 Nov 2025 -> 09 Nov 2026 (IST timestamps, backdated via created_at).
Entries <=150 chars render as "Day Snippets"; longer ones as "Deep Reflections".
Paragraph breaks are preserved by The Archives (white-space: pre-wrap).

Safe to re-run: entries already present for the account are skipped.

Usage (from backend/):
    venv/Scripts/python scripts/seed_elder_journal_v2.py               # prompts for login, inserts
    venv/Scripts/python scripts/seed_elder_journal_v2.py --dry-run     # print summary only
    venv/Scripts/python scripts/seed_elder_journal_v2.py --remove-old  # also delete the short v1 sample entries
"""
import os
import sys
import getpass
from dotenv import load_dotenv
from supabase import create_client, ClientOptions

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

TZ = "+05:30"


def P(*paragraphs):
    """Join paragraphs with a blank line, as they'd appear in a handwritten diary."""
    return "\n\n".join(p.strip() for p in paragraphs)


# (date, time, text)
ENTRIES = [
    # ════════════════════════ NOVEMBER 2025 ════════════════════════
    ("2025-11-10", "07:30", P(
        "First page. Dr. Rao says I must write something every day, even if it is only one line. So, for the record, and for whoever is reading this — which will mostly be me:",
        "My name is S. Raghavan. I am 69 years old. I was born on 14 March 1956 in Kumbakonam. I taught mathematics at the Government Higher Secondary School for thirty-four years and retired in 2016. I live in the yellow house on Temple Street with my dog Bruno, who is brown and greedy and loyal.",
        "My wife Meera passed away in October 2021. My daughter Priya lives twenty minutes away with her husband Karthik and their son Arjun. My son Vikram lives in Toronto with his wife Anjali and their children Rohan and Meenu.",
        "I am writing all of this down because there have been mornings lately when I have to search for these facts like spectacles on a cluttered table. Dr. Rao calls it 'mild cognitive impairment'. I call it the fog. Today the fog is light. Good. Let us begin.",
    )),
    ("2025-11-10", "21:20", P(
        "Priya set up this diary on the tablet this evening. She showed me the microphone button twice and then wrote the steps on a yellow sticky note and pasted it to the back of the tablet: 1) Press the orb. 2) Talk. 3) Press again. 4) Save.",
        "I felt silly talking to a machine at first, like a man ordering idli from a wall. But then I started telling it about the jasmine and the words kept coming. Meera always said I was a man who needed an audience. Now I have a very patient one.",
        "Priya hugged me at the door longer than usual. I think she is more frightened than I am. I must remember to be cheerful for her.",
    )),
    ("2025-11-12", "09:05", "Took the white Donepezil tablet with breakfast. Writing it so I don't take it twice. Ticked the box on the fridge chart."),
    ("2025-11-13", "18:10", P(
        "Spent the afternoon going through the steel cupboard. It is full of things Meera kept: wedding invitations from people whose faces I can no longer place, Arjun's first hospital bracelet, a school report of Vikram's from 1994 where I — his own father and teacher — gave him a 'B' in mathematics. He has never let me forget it. (Ha. The irony.)",
        "At the bottom was a tin of letters I wrote to Meera in 1979, before our wedding, when I was posted in Thanjavur. Terrible handwriting, worse poetry. One letter is just a long explanation of why the number seven is lonely. She kept all of them.",
        "I read four letters and then had to stop. Not from sadness exactly. More that the young man who wrote them feels like a nephew I am fond of but don't fully know.",
    )),
    ("2025-11-14", "18:30", "Found my spectacles in the fridge, next to the curd. I have no memory of putting them there. Bruno looked innocent."),
    ("2025-11-16", "19:45", P(
        "Sunday — the best day of the week, because Priya and Arjun come for lunch.",
        "Arjun is eight now. He corrected me when I said six, very politely, the way I used to correct students: 'Thatha, I think you mean eight.' He showed me a card trick he learned on YouTube. I pretended not to know how it worked. Then I taught him to multiply any two-digit number by eleven in his head — split the digits, add them, put the sum in the middle. 34 × 11 = 3, 3+4, 4 = 374. His face when it worked! The same face my best students made in 1989.",
        "For an hour I wasn't a patient. I was a teacher again. I want to remember that these Sundays happen, and that I am still useful to someone.",
        "Priya made more avial than three people could ever eat. There is a full box in the fridge, labelled in her handwriting: 'APPA — LUNCH MON & TUE'.",
    )),
    ("2025-11-20", "11:10", "Bruno and I walked to the park. Felix D'Souza waved from his gate. Cold, bright morning. The neem tree is full of parrots."),
    ("2025-11-23", "16:20", "Stood in the kitchen for two full minutes trying to find the word for the thing you boil water in. KETTLE. Kettle, kettle, kettle."),
    ("2025-11-27", "20:05", P(
        "Went to Selvam's shop for tomatoes and onions. Came back with three packets of Marie biscuits, a bar of Lifebuoy soap, and no tomatoes and no onions.",
        "Selvam is patient. He has known me for twenty years — I taught his elder brother. When I walk in now he smiles and says, 'Sir, list?' and holds out his hand. Today I had no list. He walked me through it: 'Sir, rice there? Dal there? Milk you took yesterday.' He remembers my kitchen better than I do.",
        "Priya has stuck a sign on the inside of the front door in big red letters: KEYS. LIST. PHONE. WALLET.",
        "I am a man who taught integration by parts to sixteen-year-olds for three decades, and now I need a sign on the door to leave my own house. I laughed about it, then I didn't, then I made tea and laughed again. That is how most days go.",
    )),

    # ════════════════════════ DECEMBER 2025 ════════════════════════
    ("2025-12-02", "08:15", "Woke up and reached for Meera's side of the bed. Then I remembered. Four years. The body forgets slower than the mind, it seems."),
    ("2025-12-05", "21:40", P(
        "A bad day. I want to write it honestly.",
        "I could not remember whether I had eaten lunch, so I ate again. Then I felt sick and lay down. When I got up I could not remember why I was lying down in the afternoon, and I panicked that I was ill. My heart was racing. I checked the stove four times.",
        "Then I sat in the garden and was angry at nothing in particular — at the neem tree, at the postman, at Meera for leaving first. Bruno came and lay on my feet the whole time. He didn't ask me anything. Dogs don't care if you remember lunch.",
        "Writing this at night, calmer now. Note to tomorrow-me: bad days pass. This one is already passing. Priya phoned at 8 and I told her I'd had a quiet day. Not quite true, but kind.",
    )),
    ("2025-12-09", "10:30", P(
        "Neurology appointment with Dr. Rao at 10 at Meenakshi Hospital.",
        "The memory test: she said five words and asked me to repeat them after a few minutes. Apple, table, penny… and the other two flew away like pigeons. I could do the clock-drawing perfectly though. I even put the numbers in the right places. She smiled and said, 'Once a teacher.'",
        "She says the tablets are doing what they can, and the rest is up to me: walking, sleeping well, talking to people, doing puzzles, keeping this diary. 'The diary is medicine,' she said. So here I am, taking my medicine.",
    )),
    ("2025-12-14", "17:00", "Watered the jasmine by the gate. It is flowering even in December. Meera planted it the year Vikram was born. It is older than my forgetting."),
    ("2025-12-19", "19:10", "Vikram called from Toronto. Minus twelve degrees there! I asked twice if he was eating properly. He laughed and said, 'Yes Appa, both times.'"),
    ("2025-12-22", "15:40", P(
        "Felix came over with a stepladder to help me put the old star lantern up on the verandah for Christmas — we have done this together every year since 2004, even though we are Hindus, because Meera loved the light it made on the floor.",
        "He held the ladder and I climbed two steps and then my legs went shaky and he shouted at me to come down. So he climbed, and I held the ladder, and we argued about whether it was straight. It was not straight. It never is. It is perfect.",
    )),
    ("2025-12-25", "21:30", P(
        "Christmas at the D'Souzas'. Rosie made plum cake and the famous pork vindaloo (I had the cake and avoided the vindaloo). Their granddaughter Anya, who is eleven, played 'Silent Night' on the piano with only one mistake, which she was very annoyed about.",
        "We sang carols. I don't know the words to any carol, but I hummed with great confidence.",
        "When I was leaving, Rosie handed me a slice of cake wrapped in foil, with 'RAGHAVAN — CAKE' written on it in marker. Apparently last year I left my slice on their table and she found it two days later. They didn't make me feel bad about it. They just adjusted. Good neighbours are a kind of medicine too.",
    )),
    ("2025-12-31", "23:50", P(
        "Last night of 2025. Fireworks over the temple tower. Bruno is under the bed, trembling; I gave him a biscuit and my old cardigan to lie on.",
        "I sat on the verandah and tried to remember the whole year, month by month. I could not. There are holes — whole weeks of March and August I could not find. But I remembered Arjun's card trick, and Priya's avial, and the parrots in the neem tree, and Meera's letters.",
        "Maybe that is enough. Maybe a year is not the list of its days but the handful you keep. I am still here. Still me, mostly. Happy New Year, Raghavan.",
    )),

    # ════════════════════════ JANUARY 2026 ════════════════════════
    ("2026-01-01", "09:00", P(
        "New Year resolutions, written in ink so I can be held to them:",
        "1. Walk every morning with Bruno, at least to the park and back.\n2. Write in this diary every evening, even one line.\n3. Do the newspaper crossword.\n4. Call Saroja in Madurai once a week.\n5. Be kind to myself when I forget. (The hardest one.)",
    )),
    ("2026-01-06", "14:20", "Feverish since last night. Throat like sandpaper, head like a drum. Staying in bed. Bruno is sleeping on the floor beside me, on guard."),
    ("2026-01-07", "10:45", "Still sick. Priya came with rasam, paracetamol and her worried face. She is staying the night on the sofa. I told her not to fuss. She fussed."),
    ("2026-01-08", "20:15", P(
        "Third day of this flu. Writing slowly.",
        "Priya made a chart and stuck it on the fridge with tablet times and little boxes to tick — exactly the kind of chart I used to make for students' homework. Paracetamol 8am, 2pm, 8pm. Donepezil with breakfast. Water every hour (she drew little glasses).",
        "I noticed today that I cannot remember yesterday at all. Only the feeling of being hot and heavy. Dr. Rao said on the phone that illness and fever make the memory worse for a while, like fog over a lake, and that it lifts again. I am holding on to that. I hope it lifts.",
        "Priya fell asleep sitting up on the sofa with her mouth open, exactly as she did on train journeys to Madurai when she was six. I covered her with Meera's shawl.",
    )),
    ("2026-01-10", "09:30", "Fever gone! Ate two idlis and a whole glass of coffee. Bruno very relieved — he has been sulking by the door for three days."),
    ("2026-01-14", "19:00", P(
        "Pongal today.",
        "Priya cooked sweet pongal in Amma's old brass pot, the one with the dent from when Vikram dropped it in 1991. We waited for it to boil over — 'Pongalo pongal!' — and Arjun shouted it the loudest, then asked why we were shouting at a pot.",
        "Arjun drew a kolam at the gate with rice flour. Crooked, with one side bigger than the other, and a cow that looked like a dog. It was the most beautiful kolam on Temple Street.",
        "And here is the strange thing. After lunch I sang the Pongal song my mother used to sing on the Kumbakonam verandah. Every verse. Every word. A song from 1962, perfectly intact, while I cannot tell you what I ate on Monday. Priya recorded me on her phone. She cried a little. I am glad someone has it now, outside my head.",
    )),
    ("2026-01-21", "07:55", "Left the milk on the stove and walked away. It boiled over. Nothing burned, but the kitchen smells. Rule from today: I stand there till it's done."),
    ("2026-01-26", "11:30", "Republic Day parade on TV. Stood up and saluted from the sofa like a schoolboy when the flag went up. Bruno barked at the jets."),
    ("2026-01-30", "18:40", P(
        "Felix came to return the stepladder (in January!) and I could not remember his first name. Twenty-two years of friendship. I just stood there smiling and saying 'Ah, my friend, my friend.'",
        "He knew. He said, 'It's Felix, Raghu. Like the cat food.' And we both laughed until I had to sit down.",
        "Writing it here: FELIX. Wife ROSIE. Granddaughter ANYA, plays piano. Like the cat food.",
    )),

    # ════════════════════════ FEBRUARY 2026 ════════════════════════
    ("2026-02-03", "10:00", "Karthik installed a gadget that switches off the gas automatically if I forget. Good idea. Slightly insulting. Mostly a good idea."),
    ("2026-02-08", "20:50", P(
        "Arjun's school annual day.",
        "He was a tree in the play. A very serious tree, painted green from neck to knees, arms out as branches. He had one line: 'The wind is coming!' He had been practising it for weeks — at lunch, in the car, in the bathroom.",
        "When his moment came, he shouted it so loudly that the microphone squealed and the whole hall burst out laughing. For a second his face crumpled. Then he saw me in the second row giving him two thumbs up, and he stood even straighter, the proudest tree in Tamil Nadu.",
        "I held Priya's hand through the rest of the play. I want to keep this one. A serious little tree with a very loud voice.",
    )),
    ("2026-02-13", "15:30", "Sorting the photo albums. Found Meera in her yellow silk saree at the Mysore Palace, 1981, squinting into the sun and laughing at me for taking too long."),
    ("2026-02-14", "21:00", P(
        "Valentine's Day. We never celebrated it — Meera called it 'a greeting-card company's festival' and refused to let me buy roses. Once I bought one anyway and she put it in a steel tumbler on the TV and pretended to be annoyed for three days.",
        "Today I put the Mysore photo on the dining table and talked to her for a while over my dinner. I told her about Arjun the tree. I told her the fog is sometimes thick now. I told her I sometimes forget she's gone, and then I lose her again, fresh, like the first morning.",
        "I think she would say, 'So? You never remembered where you kept the umbrella either. You'll manage.' She would be right. She always was, irritatingly.",
    )),
    ("2026-02-19", "12:15", "Paid the electricity bill online with Priya's help. Then nearly paid it again an hour later. Wrote PAID across the bill in big red letters."),
    ("2026-02-25", "17:45", P(
        "Felt dizzy watering the garden at 2 o'clock, in full sun. I realise now I hadn't drunk a drop of water since breakfast coffee — just forgot.",
        "Had to sit on the step with my head between my knees. Better after a big glass of water and a banana. Did not tell Priya. Telling the diary instead.",
    )),

    # ════════════════════════ MARCH 2026 ════════════════════════
    ("2026-03-03", "19:30", P(
        "Holi! Priya's family came in old clothes, armed.",
        "Arjun ambushed me at the gate and emptied a whole packet of green powder over my white kurta. I got him back with pink. Karthik got us both with the water pistol. Bruno was turned partly purple and is deeply offended.",
        "I have green in my ears even after two baths. Worth it.",
    )),
    ("2026-03-08", "10:20", P(
        "I got lost today. I must write it properly, because Dr. Rao needs to know and because I don't want to pretend it didn't happen.",
        "I walked to the temple at 7 for the morning pooja, as I have done a thousand times. Coming back, I turned at the banyan tree, and suddenly nothing was right. The houses looked like photographs of themselves. I knew I lived nearby but I could not find the thread. I walked one way, then back. For about twenty minutes. My shirt was wet with sweat and my heart was pounding.",
        "A young auto driver stopped and said, 'Raghavan Sir? You taught my father, Murugan, 1988 batch!' He drove me home — four streets — and refused to take money. He said his father still talks about my 'magic triangles'.",
        "I sat on the verandah shaking for an hour. Then I phoned Priya and told her everything. She was quiet, then very practical. That is how she copes. That is how I cope too. We are the same.",
    )),
    ("2026-03-09", "09:10", "Priya bought me a watch that shows where I am on her phone. I thought I would mind. I don't. It feels like holding a hand."),
    ("2026-03-14", "22:10", P(
        "My 70th birthday. Seventy! I am writing this late because I don't want to lose a single piece of it.",
        "Priya told me we were 'just having lunch'. I came out in my old veshti. The house was full. Balloons on the ceiling fan. Vikram on a video call on the big TV from Toronto at 2am his time, with Anjali and the children in pyjamas. Rohan and Meenu sang 'Happy Birthday' in Tamil with Canadian accents and I laughed so much I cried.",
        "Then my old colleagues walked in — Subbu, who taught chemistry and set fire to a lab coat in 1993, and Lakshmi teacher, who still calls me 'Mr. Strict'. Subbu brought the staff photograph from 1994. I remembered every single face in it, and every name. Every one. Isn't that something?",
        "Arjun gave me a card he made himself: 'THATHA. You are the best at maths and the worst at finding keys. Happy 70.' Both entirely true. I have stuck it on the fridge.",
        "Felix and Rosie brought a cake shaped like a slide rule. Felix made a speech and forgot the end of it, and said, 'Well, it's catching, Raghu.' Best day in a very long time.",
    )),
    ("2026-03-15", "08:30", "Woke up and saw the balloons tied to the fan and for a moment didn't know why. Then I read yesterday's entry. Seventy, and happy."),
    ("2026-03-22", "16:00", P(
        "Planted tomato and chilli seedlings in the side garden with Arjun.",
        "He insisted every plant needs a name. The biggest tomato is 'Gerald'. The chillies are 'Spicy One', 'Spicy Two' and 'Mr. Hot'. He wrote the names on ice-cream sticks and pushed them in the soil. He made me promise to water Gerald every day and 'tell him he's doing good'.",
        "I have written a note on the kitchen whiteboard: WATER GERALD. Talk nicely.",
    )),
    ("2026-03-28", "20:00", "BP high at the clinic: 160/95. Less salt, Dr. Rao says. No more pickle with curd rice. What is the point of curd rice without pickle?"),

    # ════════════════════════ APRIL 2026 ════════════════════════
    ("2026-04-02", "11:40", "Already very hot. Bruno sleeps on the cool bathroom floor every afternoon. Smartest one in this house."),
    ("2026-04-07", "21:20", P(
        "Something happened today that I need to write down so I never make my daughter do it again.",
        "Priya says that this afternoon, on the phone, I asked her when Amma was coming back from Chitra Aunty's house. I don't remember asking. She told me tonight, very gently, sitting next to me on the sofa with her hand on my arm.",
        "Meera — Amma — passed away on 24 October 2021, in the Meenakshi Hospital, at 4:10 in the morning. Priya was holding one hand and I was holding the other. Her heart. It was quick, in the end.",
        "I am writing it here in plain words, Raghavan, so that when you read this and wonder, you will know. And you will be sad again. But you will not ask Priya, because it breaks her heart to tell you.",
        "I feel as if I lost Meera twice today. I sat with her photo for a long time. Then I watered Gerald, because he is doing good, and somebody has to tell him.",
    )),
    ("2026-04-14", "09:45", P(
        "Tamil New Year — Puthandu.",
        "Priya made mango pachadi: raw mango, jaggery, neem flowers, chilli, salt, tamarind. Sweet, sour, bitter, hot, salty. All the tastes of life in one bowl, Amma used to say, and you must eat all of it, not pick out the sweet bits.",
        "I explained this to Arjun. He picked out the sweet bits.",
    )),
    ("2026-04-18", "18:10", P(
        "Walked to the park and back with Bruno at 6:30, before the heat. Then did the newspaper crossword: 17 out of 20 clues before lunch!",
        "'Seven letters, a calculating device' — ABACUSES? No. ABACI? Too short. Gave up on that one. Still a very good score for an old brain. Remembered Selvam's whole list without paper too.",
    )),
    ("2026-04-25", "15:00", "Gerald the tomato has a yellow flower! Phoned Arjun at once. He screamed so loudly on the phone that Bruno barked."),

    # ════════════════════════ MAY 2026 ════════════════════════
    ("2026-05-02", "20:40", P(
        "Our wedding anniversary. Forty-six years, if she were here.",
        "I went to the temple early and lit a ghee lamp for her. The priest, who was a small boy when we married, remembered the date before I told him.",
        "When I came home I could not remember what year we married. It frightened me badly — I stood in the kitchen and tried and tried. Then I made her favourite, curd rice with pomegranate seeds and a little ginger, and while I was stirring it, it came back all at once: 1980. The second of May. Rain all morning. Her father pacing outside the hall with an umbrella, convinced it was a bad omen. Meera laughing at him with jasmine falling out of her hair.",
        "It came back. Some things come back if you are patient and you stir slowly. I ate the curd rice on the verandah where we used to sit, and the neighbours' radio was playing an old Ilaiyaraaja song, and it felt like she'd arranged it.",
    )),
    ("2026-05-06", "13:30", "Too hot to walk. Re-reading 'The Man Who Knew Infinity'. Third time? Fourth? Every time I'm surprised by the ending, which is one advantage of my condition."),
    ("2026-05-11", "07:20", "Fell asleep in the armchair and woke at 4am convinced it was evening. Made dinner. Ate it. Then the birds started and I understood. Confusing."),
    ("2026-05-17", "19:15", "Arjun and I counted the ripe tomatoes: eleven. Gerald alone gave five. Arjun made me write the number down 'for science'. 11."),
    ("2026-05-24", "21:30", P(
        "Started the memory group at the community hall today. Tuesdays, 10 to 12.",
        "There are eight of us, all grey heads. A retired bank manager, a former bus conductor, a lady who used to run a tailoring shop, and Kamala, who was a nurse for forty years at the government hospital and now forgets her own daughter's phone number, just like me.",
        "The facilitator, a young psychologist named Divya, made us play memory games and then talk about how we feel. I expected to hate it. Instead we laughed more than I've laughed in months. Kamala told a story about putting her slippers in the rice tin, and the bus conductor said he'd once got on the wrong bus — his own route — and asked the conductor where it was going.",
        "It is easier to laugh with people who are in the same boat. We are all rowing the same leaky boat, and nobody is pretending it isn't leaking.",
        "Divya gave us homework: write down three good things every day. Homework! At seventy! I have done it: 1) Kamala's slipper story. 2) Cold buttermilk. 3) Bruno.",
    )),
    ("2026-05-29", "16:45", "Five-hour power cut. Sat outside with Felix in the shade. He talked about growing up in Goa; I listened. Fine afternoon."),

    # ════════════════════════ JUNE 2026 ════════════════════════
    ("2026-06-03", "08:00", P(
        "First rain of the monsoon!",
        "It came at 6 in the morning, sudden and heavy. The whole street smelled of wet earth, that smell there is a word for — petrichor. (Remembered the word! Wrote it down so as not to lose it.)",
        "I stood in the garden in my banian and let it soak me through, the way I did as a boy in Kumbakonam. Felix saw me from his window and shouted, 'Raghu, you'll catch your death!' I shouted back, 'Then I'll catch it happy!'",
    )),
    ("2026-06-04", "10:30", "Sneezing and sniffling since yesterday. That is what standing in the rain at seventy gets you. Felix has been insufferable about it."),
    ("2026-06-09", "17:20", P(
        "Memory group: we each brought one photograph and told its story.",
        "I took the 1994 staff photograph. I told them about each teacher — who was strict, who was kind, who cried at farewells. Subbu with his singed eyebrows. Lakshmi teacher who kept a cane she never once used. The headmaster who thought computers were a passing fashion.",
        "Kamala brought a photo of herself in her nurse's uniform, 1979, so young and straight-backed. She held it up and said, 'This one knew everything. I'm the one who has to find it all again.' Nobody said anything for a moment. Then Divya said, 'And look how well you're doing.' We clapped for Kamala.",
    )),
    ("2026-06-15", "20:20", P(
        "Father's Day. Not a Tamil custom, but the children like it, so I like it.",
        "Vikram called early in the morning — evening in Toronto — and we talked for nearly an hour, about cricket mostly, and about his work, which I understand less every year (something with 'cloud'). He asked me three times if I was taking my medicine. I said yes three times. Now I know how he felt in December.",
        "Priya brought a framed drawing from Arjun: me with Bruno and a tomato almost as big as Bruno, labelled GERALD. In the drawing I am smiling with all my teeth, which I don't have anymore.",
        "I have hung it on the wall beside the front door, right next to KEYS. LIST. PHONE. WALLET. It feels right that they are together. Things to remember, and the reason to.",
    )),
    ("2026-06-21", "07:00", "International Yoga Day. Did five minutes of stretching on the verandah. My knees made noises like a pressure cooker."),
    ("2026-06-27", "12:40", "Could not find the TV remote anywhere. It was in the bread box. Bruno is not a suspect, but I questioned him anyway."),

    # ════════════════════════ JULY 2026 ════════════════════════
    ("2026-07-04", "22:00", P(
        "VIKRAM IS HOME!",
        "Flew in from Toronto with Anjali and the two children for three whole weeks. The house is so loud — suitcases in the hall, the children's voices bouncing off the walls, the smell of Anjali's coffee. I didn't realise how quiet it had become.",
        "I kept calling Meenu 'Priya', which made everybody laugh, and Rohan corrected me very patiently each time: 'Thatha, I'm Rohan. R-O-H-A-N.' He is eleven and taller than his mother already.",
        "So I've written everybody's names on the kitchen whiteboard in big letters with their ages:\nVIKRAM (43) — my son\nANJALI — his wife, makes good coffee\nROHAN (11) — tall, likes cricket\nMEENU (7) — named after Meera",
        "Meenu came and sat in my lap tonight and asked me to tell her about her Paati. So I told her about the yellow saree in Mysore, and the rose in the steel tumbler, and how Paati laughed. She fell asleep before the end. I didn't mind.",
    )),
    ("2026-07-09", "18:30", P(
        "Took the whole family to Mahabalipuram for the day.",
        "Rohan climbed every rock and every carving and was shouted at by a security guard twice. Vikram and Karthik argued about directions. Arjun and Meenu buried each other's feet in the sand and built a 'temple' that was mostly a pile.",
        "I sat with Meenu by the shore temple while the others went to see Arjuna's Penance. She asked why the sea doesn't run out. I told her it's like love — it goes out and always comes back. She said that wasn't a scientific answer. She is absolutely right. Named after her grandmother indeed.",
    )),
    ("2026-07-14", "21:10", P(
        "Vikram sat with me late tonight on the verandah after everybody was asleep, and asked me how I really am. Not the polite answer, he said. The real one.",
        "So I told him the truth. Some mornings I wake up and the room is a stranger, and I lie still and wait for it to introduce itself. Sometimes I read this diary to find out who I am that day. Sometimes I forget his mother is gone. Sometimes I am frightened of the day when I won't recognise his face.",
        "He cried. My son, forty-three years old, a manager in a big Canadian company, crying at his father's kitchen table like a boy who has scraped his knee. I held his head like I did when he was five.",
        "I told him what my own father told me when his eyes were failing: you don't have to fix it, kanna. You only have to visit. He promised to call every Sunday, without fail. I am writing that down so I can hold him to it.",
    )),
    ("2026-07-25", "06:30", "They left for the airport at 4am. The house is far too quiet now. Bruno keeps checking the guest room and coming back confused."),
    ("2026-07-28", "15:10", "Found a drawing from Meenu under my pillow. A big red heart and, in careful letters: 'THATHA DON'T FORGET ME'. I won't, kanna. I'll keep it right here."),

    # ════════════════════════ AUGUST 2026 ════════════════════════
    ("2026-08-04", "09:00", "Felt light-headed standing up from the bed and slipped in the bathroom. Hip hurts badly. Called Priya. Writing this from the floor."),
    ("2026-08-04", "22:45", P(
        "Hospital. Writing on Priya's phone with one finger.",
        "The X-ray shows no fracture, thank God — just a very deep bruise on the hip and a scrape on my elbow. They are keeping me overnight 'for observation', which means being woken every two hours by kind nurses with cold hands.",
        "Every time, they ask me the date and the name of the Prime Minister. I got the Prime Minister right every time. I got the date wrong every time. At 9pm I told the nurse it was 1998. She wrote something on her clipboard and patted my hand. Now I can't stop thinking about what she wrote.",
        "Priya is asleep in the plastic chair beside the bed with her mouth open, exactly as she did as a little girl on the night train to Madurai. She came straight from work and has not left.",
        "I am frightened of being a burden to her. I'm writing so that I remember: she stayed. She stayed all night.",
    )),
    ("2026-08-06", "14:00", "Discharged. Walking with a stick now — Meera's father's old wooden one with the silver tip. Karthik fitted a rubber mat and a grab bar in the bathroom."),
    ("2026-08-10", "19:30", P(
        "Hip still sore. A dark mood all day.",
        "Sat by the window for most of the afternoon and didn't want to write or read or talk. Didn't do the crossword. Didn't do Divya's three good things. Couldn't think of one.",
        "Then Bruno brought me his ball, very seriously, and dropped it on my foot, and kept looking at me until I threw it — badly, from the chair. He brought it back. I threw it again. We did this for twenty minutes.",
        "So, one good thing: Bruno doesn't accept dark moods.",
    )),
    ("2026-08-15", "10:15", "Independence Day. Watched the flag hoisting at the corner with Felix. Stood up straight for the anthem, stick and all. Didn't wobble once."),
    ("2026-08-22", "20:00", "Physio exercises done, all three sets. The physio, Revathi, says I am 'very disciplined'. Thirty-four years of setting homework — of course I am."),
    ("2026-08-28", "21:00", P(
        "Raksha Bandhan was yesterday, Priya says, and I completely missed it — didn't call my sister Saroja in Madurai, for the first time in over sixty years.",
        "I phoned her this morning to apologise. She laughed her big laugh and said she'd forgotten too, and only remembered when her granddaughter tied a rakhi on her son. 'Two old people forgetting each other,' she said, 'is still remembering, in its own way.'",
        "Then we talked for an hour about our father's black Hercules bicycle — how he carried both of us on it to the Kumbakonam temple festival, Saroja on the handlebars and me on the carrier, and how he fell into the ditch by the tank and came up covered in mud and lotus leaves and still laughing.",
        "I had forgotten that story completely. Saroja gave it back to me. Sisters are archives too.",
    )),

    # ════════════════════════ SEPTEMBER 2026 ════════════════════════
    ("2026-09-04", "08:45", "Walked to the park without the stick today! Slowly, like a tortoise. Bruno waited for me at every corner, looking back over his shoulder."),
    ("2026-09-05", "20:10", P(
        "Teachers' Day.",
        "Three former students messaged me — Priya showed me on her phone and then saved them for me.",
        "One is Dr. Senthil, now a professor of mathematics at a university in Pune. He wrote: 'Sir, you made me love numbers. I still use your triangle method in my first-year lectures and I tell students it's the Raghavan Method.' The Raghavan Method! I didn't know I had a method.",
        "Another, Fathima, is a civil engineer who builds bridges in Kerala. She said I was the only teacher who told her girls could be engineers. I don't remember saying it, but I am very glad I did.",
        "I read the messages many times today. I may forget that I read them. But they will be here, in the Archives, and I can read them again tomorrow and be just as happy all over again. That is the strange gift of a bad memory: good news stays new.",
    )),
    ("2026-09-11", "11:30", "Dr. Rao: memory scores stable since March. 'Stable is good,' she says. Stable I'll take. Stable, and a cup of filter coffee on the way home."),
    ("2026-09-14", "19:00", P(
        "Ganesh Chaturthi.",
        "Arjun made a clay Ganesha at school and brought him home very carefully in a shoebox. Halfway up the steps the trunk fell off. Arjun was devastated. We fixed it with a toothpick and some glue and called him 'Toothpick Pillaiyar'.",
        "We did the pooja together and Arjun rang the bell so hard it fell off its chain. It was that kind of day. Lord Ganesha is the remover of obstacles. Today he removed a trunk and a bell.",
    )),
    ("2026-09-19", "16:30", "Couldn't remember if I had fed Bruno. Bruno insisted, very convincingly, that I had not. Checked the chart: I had. Bruno lies."),
    ("2026-09-26", "21:45", P(
        "Woke up from my afternoon nap absolutely certain I was late for school. I had to give a test to Class 10-B, the troublesome section, and I hadn't finished setting the paper.",
        "I put on a shirt, found my old leather briefcase in the cupboard, and was looking for my bicycle clips before I understood. Retired since 2016. Ten years. Class 10-B are all in their thirties now with children of their own.",
        "It was frightening, and then it was a bit funny, and then I sat down on the bed and wrote this so I could see it in daylight.",
        "Felix came by at five. I told him I had almost gone to teach. He said, 'Well, then, teach me something.' So I taught him the trick with the number 1089: take any three-digit number, reverse it, subtract the smaller, reverse the answer, add — always 1089. He tried it four times, suspicious. Always 1089. He called me a magician. For one evening I was.",
    )),

    # ════════════════════════ OCTOBER 2026 ════════════════════════
    ("2026-10-02", "10:00", P(
        "Gandhi Jayanti. Cleaned the garden shed as a small act of seva, as Gandhiji would have wanted, and as Meera had been asking me to for about eleven years.",
        "Found her gardening gloves on the top shelf — green cotton, with a hole in the right thumb she kept meaning to mend. Still smelling faintly of soil and her coconut oil. I put them on. They're too small for me. I wore them anyway to pull the weeds by the jasmine.",
    )),
    ("2026-10-08", "13:15", "Cough, and my chest feels heavy. Doctor says a chest infection. Antibiotics, twice a day for five days. Resting."),
    ("2026-10-10", "18:20", "Still coughing at night. Priya brought a steam inhaler and a hot water bottle and sat with me. Bruno has moved his bed next to mine again."),
    ("2026-10-13", "09:30", "Cough nearly gone. Bruno and I sat in the sun for a whole hour doing nothing. Medicine of the best kind."),
    ("2026-10-19", "20:30", P(
        "Navaratri. Priya set up the golu steps in the front room.",
        "The old dolls came out of the trunk — the ones from Meera's mother, wrapped in newspapers from 1998, whose headlines I read one by one as I unwrapped (a cricket match against Pakistan, the price of onions — some things never change).",
        "And here is the wonderful thing. I didn't have to think about where they went. My hands just knew. The wedding procession on the third step. The Chettiar and his wife and their little shop at the bottom. Dasavataram along the top, in order. The wooden marapachi couple in the centre, a little faded, because they were Meera's favourites.",
        "Priya stood back and let me arrange the whole thing exactly as her mother used to. When I finished she said, 'It looks like Amma's golu.' My hands remembered what my head did not. I think that is where Meera is now — in my hands.",
    )),
    ("2026-10-21", "11:00", P(
        "Vijayadashami. Vidyarambham for Arjun, though he already reads better than I do these days.",
        "Priya spread rice on a brass plate and I held Arjun's finger and guided it to write 'அ', the first letter, and then 'Om' in Sanskrit. My own father did this for me in 1959, in Kumbakonam, I'm told — I don't remember it. But Arjun will. That's the point. It passes on.",
    )),
    ("2026-10-24", "17:50", P(
        "Fifth death anniversary of Meera. Five years. (Corrected myself — Priya says five. I had written four.)",
        "Went to the temple with Priya and Karthik in the morning and did the tharpanam. Lit a lamp at home in front of her photo — the yellow saree, Mysore. Made her curd rice with pomegranate.",
        "I didn't cry today. I remembered her laugh instead — the big one, the one that embarrassed her in cinema halls. I remembered it so clearly I almost heard it. That is a good kind of anniversary, I think.",
    )),
    ("2026-10-27", "12:30", "Head full of cotton wool this morning. Missed memory group — completely forgot it was Tuesday. Kamala called at noon to check on me."),
    ("2026-10-30", "19:15", P(
        "Kamala and I had coffee at the Udupi hotel after the make-up session at the hall. We talked for two hours.",
        "She told me she is frightened of the day she won't know her grandchildren. I told her about Meenu's drawing — 'THATHA DON'T FORGET ME' — and how I keep it in my wallet. She took out her own wallet and showed me a drawing from her granddaughter: a stick-figure nurse with a giant red cross and the words 'BEST PAATI'.",
        "We sat there, two old forgetful people with crayon drawings in our wallets, and decided that if we ever forget them, at least the drawings won't forget us.",
    )),

    # ════════════════════════ NOVEMBER 2026 ════════════════════════
    ("2026-11-03", "19:40", P(
        "Arjun's ninth birthday. Nine!",
        "Party at Priya's house. The cake was shaped like a cricket bat, complete with a chocolate ball. Twelve shrieking nine-year-olds. Karthik organised musical chairs and nearly lost to a girl named Diya.",
        "My present for Arjun: my old geometry box from 1971 — the steel compass, the protractor with the 90° mark worn off, the set squares with 'S. RAGHAVAN, X-A' scratched into them. I polished it all yesterday.",
        "He opened it very slowly, as if it were treasure, and then said, 'Thatha, will you teach me how to use all of these?' I said yes. I am writing it here so I keep the promise, even on foggy days. ARJUN — GEOMETRY BOX LESSONS. Sundays.",
    )),
    ("2026-11-06", "16:00", "Diwali shopping with Priya at T. Nagar. Chose a big sparkler box for Arjun and a new collar for Bruno. Remembered the whole list without looking!"),
    ("2026-11-08", "22:30", P(
        "Diwali.",
        "The whole of Temple Street was lit tonight — lamps on every wall, the D'Souzas' Christmas star already up 'to be on the safe side', children with sparklers everywhere, Bruno under the bed with my cardigan.",
        "Priya, Karthik and Arjun came early for the oil bath and new clothes. Felix and Rosie came for sweets and stayed for dinner. And at 7pm, Vikram's whole family joined on the big TV from Toronto — 8:30 in the morning there, all of them still in pyjamas, Meenu holding up her own little clay lamp to the screen.",
        "Arjun had an idea: he and I lit seventy lamps along the front wall — one for every year of my life. It took forever. Rosie counted, out loud, in Konkani. When the last one was lit, everybody clapped, and Vikram on the TV said, 'Appa, that's a lot of years,' and I said, 'And I remember most of them.'",
        "I forgot to take my medicine at dinner; Priya reminded me. But I did not forget a single face tonight. Not one.",
    )),
    ("2026-11-09", "08:20", P(
        "Today I read the first page of this diary, from almost exactly one year ago.",
        "My name is still S. Raghavan. I am 70 now, not 69. I still live in the yellow house on Temple Street, with Bruno, who is still greedy and loyal. Meera is still gone, and I still miss her. Priya and Karthik and Arjun are still twenty minutes away. Vikram still calls every Sunday — he kept his promise.",
        "The fog comes and goes. Some mornings are harder than they were a year ago. But I have this now: a whole year of myself, written down, that I can open whenever I'm lost. A serious little tree. A tomato named Gerald. A song from 1962. Seventy lamps.",
        "Thank you, notebook-thing. Let's do another year.",
    )),
]


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN ENTRIES — recurring cause → effect loops for the Blindspots engine.
# Each loop repeats 4-7 times across the year; the trigger is usually written
# the day before the effect so the analyser can connect them across time.
#
#  NEGATIVE  late-night TV            → foggy, confused, lost things next day
#  NEGATIVE  days alone, nobody to talk to → skipped meals/tablets, confusion
#  NEGATIVE  not drinking water in heat   → dizziness, light-headedness, the fall
#  NEGATIVE  salty pickle/papad feasts    → BP spike + headache next day
#  POSITIVE  early morning walk with Bruno → clear head, high crossword scores
#  POSITIVE  teaching maths (Arjun/Felix)  → sharp recall, good mood after
#  NEUTRAL   hides bad days from Priya ("told her I was fine")
# ─────────────────────────────────────────────────────────────────────────────
PATTERN_ENTRIES = [
    # ── late-night TV → next-day fog ──
    ("2025-12-04", "23:55", "Stayed up till 1:30 watching the old Sivaji Ganesan film 'Pasamalar' on Raj TV. Cried at the end as always. Too awake to sleep now."),
    ("2026-01-17", "23:50", "India vs Australia one-day match went to the last over. Stayed up till nearly 2am. Worth it — we won by two wickets!"),
    ("2026-01-18", "13:10", P(
        "A muddled, heavy day. Couldn't find my keys (in the bathroom), then my wallet (in Bruno's basket — how?), then my spectacles (on my head).",
        "When Priya phoned I called her 'Meera' by mistake. She went quiet. I said I was just tired. My head feels like it's full of wet cotton.",
    )),
    ("2026-03-07", "23:40", "Test match highlights and then an old MGR film. It's past 2am. I'll sleep late tomorrow — no harm in it."),
    ("2026-05-10", "23:59", "Watched the whole Ilaiyaraaja concert re-run on TV — three and a half hours. Sang along to every song. Bed at 1am."),
    ("2026-06-12", "23:45", "Couldn't sleep, so I watched two old black-and-white films back to back. Bed around 2."),
    ("2026-06-13", "15:20", P(
        "Strange, slow day. Put sugar in the rasam instead of salt. Left the front gate open and Bruno went visiting the whole street.",
        "The gas cylinder man came and I had no memory of booking it — Priya had. I had to sit down for a while because nothing felt quite in its right place.",
    )),
    ("2026-09-25", "23:50", "Late night again — a Sivaji film festival on TV all week. Watched till nearly 2. I know, I know."),
    ("2026-10-26", "23:55", "World Cup qualifier went into a super over. Couldn't switch off. Bed after 1:30."),
    ("2026-07-02", "21:15", P(
        "In bed by 9:30 every night this week, TV off by 9 — Divya from the memory group suggested it.",
        "I have noticed something: the mornings are clearer. I found my keys on the hook three days in a row. Writing it here so I don't forget the reason.",
    )),

    # ── isolation → confusion / skipped meals and tablets ──
    ("2025-11-30", "20:30", "Priya, Karthik and Arjun are at Karthik's parents' in Salem for the weekend. Felix is at a wedding. Didn't speak to a single person today except Bruno."),
    ("2025-12-01", "19:40", "Second quiet day. Forgot to eat lunch — found the box of avial untouched at 6pm. Not sure if I took the tablet. The house echoes."),
    ("2026-04-04", "19:00", "Priya has gone to Coimbatore for a cousin's wedding until Tuesday. Felix and Rosie are in Goa. Nobody came today. I watched TV and talked to Bruno."),
    ("2026-04-06", "20:10", P(
        "Third day alone. I didn't go out at all. Ate biscuits for lunch and forgot dinner until 10pm.",
        "Found yesterday's tablet still in the box. Kept walking from room to room looking for something and never knowing what. I set two plates at the table tonight without thinking.",
    )),
    ("2026-07-27", "19:30", "Second day since Vikram's family left. Didn't go out, didn't phone anyone. Sat in the guest room for a long time. Nobody to talk to."),
    ("2026-07-29", "20:45", P(
        "Found two days of tablets still in the weekly box — Tuesday and Wednesday. Didn't eat lunch today either. I seem to have lost the thread of the days since the house went quiet.",
        "When Priya phoned, I told her I'd had a lovely lunch and was fine. I hadn't eaten lunch. I'm not fine.",
    )),
    ("2026-08-08", "18:00", "Third day indoors with the sore hip. Priya busy with office audits, Felix down with a cold. No visitors. The days are running together."),
    ("2026-08-09", "20:00", "Forgot my evening tablet and couldn't remember if I had eaten. Kept asking Bruno what day it was. He didn't know either."),

    # ── dehydration / heat → dizziness ──
    ("2026-04-22", "14:30", "Walked to Selvam's shop at 1pm in the full heat and forgot my water bottle. Very dizzy at the gate coming back — had to hold the wall and sit down."),
    ("2026-05-20", "21:30", "Realised tonight I drank only two glasses of water all day — just forgot. Leg cramps, and the room swam when I stood up from the chair."),
    ("2026-08-03", "22:15", "Very hot, sticky day. Noticed at bedtime that the water jug Priya fills every morning is still almost full. I barely drank anything. Feeling weak and a bit woozy."),
    ("2026-09-08", "19:00", "Priya's new system: a big steel jug with lines marked 9am, 12, 3pm, 6pm. Drank down to every line. Steady on my feet all day — no dizziness at all."),

    # ── salty food → BP spike next day ──
    ("2026-01-15", "11:00", "Pongal feast yesterday — vadai, papad, two kinds of pickle. Thumping headache this morning. BP on the home machine: 152/94."),
    ("2026-03-27", "21:00", "Rosie sent a jar of her Mangalorean lime pickle. Delicious. I ate nearly half of it tonight with curd rice. Worth it."),
    ("2026-06-29", "22:30", "Selvam's son's wedding feast. Ate papad, pickle, and the very salty chips — far too much. Came home very happy."),
    ("2026-06-30", "10:30", "Headache since waking, and puffy ankles. BP on the home machine: 158/96. Dr. Rao's voice in my head: 'less salt, Mr. Raghavan.'"),
    ("2026-10-22", "09:40", "Navaratri week of sundal, vadai and pickles with every meal. Pounding headache today. BP 155/94 this morning."),

    # ── morning walk → clear-headed days ──
    ("2025-11-20", "19:30", "Remarkably clear day after the morning walk. Remembered every name at the park — Felix, the jogging doctor, the parrot man. Crossword 16 of 20."),
    ("2026-01-03", "18:00", "Third morning walk in a row with Bruno, 30 minutes. Crossword 17 of 20 by lunchtime. Remembered every name at the temple. My head feels rinsed clean."),
    ("2026-02-10", "18:30", "Rain all morning, no walk for the third day. Crossword only 8 of 20. Lost my keys twice. Felt slow and grumpy all afternoon."),
    ("2026-06-24", "17:00", "Monsoon rain every morning this week — no walks since Saturday. Foggy-headed, short-tempered with Bruno, crossword barely half done."),
    ("2026-06-26", "18:45", "Rain stopped! Long walk at 7am — 45 minutes, round the temple tank twice. Clearest day in a week. Crossword 18 of 20 and found the electricity bill I'd lost."),
    ("2026-10-15", "18:20", "Walked 40 minutes before breakfast, all the way to the old school gate and back. Crossword 18 of 20. Recited all of Anya's and Arjun's friends' names at tea."),

    # ── teaching maths → sharp recall ──
    ("2025-11-17", "18:00", "Still feeling sharp after yesterday's lesson with Arjun. Recited the tables up to 20 while cooking. Found the gas bill I'd lost for a week."),
    ("2026-02-22", "19:20", P(
        "Sunday geometry lesson with Arjun — I showed him how to bisect an angle with only a compass. He did it perfectly on the third try.",
        "Afterwards I felt wonderfully sharp. I remembered where I'd hidden the bank passbook (inside the Bhagavad Gita!) and Saroja's phone number without looking.",
    )),
    ("2026-06-07", "20:00", "Spent the afternoon setting maths puzzles for Arjun — magic squares. Clear and cheerful all evening. Did Divya's three good things in two minutes flat."),
    ("2026-09-27", "10:30", "Woke clear-headed after teaching Felix the 1089 trick last night. Remembered all of Class 10-B's toppers from 2009 over coffee. Funny how teaching tidies the mind."),
    ("2026-11-04", "18:30", "First geometry box lesson with Arjun — how to use the protractor. Felt bright as a new pencil all afternoon. Remembered Rosie's birthday before she did."),

    # ── hides bad days from Priya (coping) ──
    ("2026-01-19", "20:00", "Priya asked if yesterday's 'Meera' slip meant anything. I told her it was nothing, just tired eyes. I didn't tell her about the wallet in Bruno's basket."),
    ("2026-05-11", "19:00", "Told Priya on the phone that I'd slept beautifully. I didn't tell her about cooking dinner at 4am. No need to worry her."),
    ("2026-08-05", "08:30", "In the hospital I told Priya the fall was just a wet floor. I didn't tell her I'd felt woozy all the night before and hardly drank any water."),
    ("2026-10-28", "20:30", "Told Priya I'd 'chosen to skip' memory group yesterday to rest. Truth is I forgot entirely. Why do I keep pretending to her?"),
]


def all_entries():
    return sorted(ENTRIES + PATTERN_ENTRIES, key=lambda e: (e[0], e[1]))


def build_rows(profile_id):
    return [
        {
            "content": text,
            "profile_id": profile_id,
            "created_at": f"{date}T{time}:00{TZ}",
        }
        for date, time, text in all_entries()
    ]


def old_v1_contents():
    """Contents of the short v1 sample entries (scripts/seed_elder_journal.py)."""
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from seed_elder_journal import ENTRIES as V1_ENTRIES
    except ImportError:
        return []
    return [text for _, _, text in V1_ENTRIES]


def main():
    dry_run = "--dry-run" in sys.argv
    remove_old = "--remove-old" in sys.argv

    if dry_run:
        rows = build_rows("dry_run_user")
        for r in rows:
            kind = "SNIPPET   " if len(r["content"]) <= 150 else "REFLECTION"
            first_line = r["content"].split("\n")[0]
            print(f"{r['created_at']}  {kind}  {len(r['content']):5d} chars  {first_line[:70]}")
        snippets = sum(1 for r in rows if len(r["content"]) <= 150)
        total_chars = sum(len(r["content"]) for r in rows)
        print(f"\n{len(rows)} entries ({snippets} snippets, {len(rows) - snippets} reflections), {total_chars:,} characters")
        return

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        print("SUPABASE_URL / SUPABASE_ANON_KEY missing from backend/.env")
        sys.exit(1)

    email = input("Email of the account to seed: ").strip()
    password = getpass.getpass("Password: ")

    auth = create_client(url, key)
    session = auth.auth.sign_in_with_password({"email": email, "password": password})
    user_id = session.user.id
    token = session.session.access_token
    print(f"Authenticated as {email} ({user_id})")

    sb = create_client(url, key, options=ClientOptions(headers={"Authorization": f"Bearer {token}"}))

    if remove_old:
        removed = 0
        for text in old_v1_contents():
            res = sb.table("journal_slates").delete().eq("profile_id", user_id).eq("content", text).execute()
            removed += len(res.data or [])
        print(f"Removed {removed} short v1 sample entries.")

    existing = sb.table("journal_slates").select("content").eq("profile_id", user_id).execute()
    existing_contents = {row["content"] for row in (existing.data or [])}

    rows = [r for r in build_rows(user_id) if r["content"] not in existing_contents]
    skipped = len(all_entries()) - len(rows)
    if rows:
        sb.table("journal_slates").insert(rows).execute()
    print(f"Inserted {len(rows)} diary entries into The Archives (Nov 2025 - Nov 2026)."
          + (f" Skipped {skipped} already present." if skipped else ""))


if __name__ == "__main__":
    main()
