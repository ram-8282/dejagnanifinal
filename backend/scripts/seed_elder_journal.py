"""
Seed The Archives with one year of journal entries written in the voice of a
70-year-old retired maths teacher living with early memory loss.

Span: 10 Nov 2025 -> 09 Nov 2026 (local IST timestamps, backdated via created_at).
Entries <=150 chars render as "Day Snippets"; longer ones as "Deep Reflections".

Usage (from backend/):
    venv/Scripts/python scripts/seed_elder_journal.py            # prompts for login, inserts
    venv/Scripts/python scripts/seed_elder_journal.py --dry-run  # just prints the entries
"""
import os
import sys
import getpass
from dotenv import load_dotenv
from supabase import create_client, ClientOptions

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

TZ = "+05:30"

# (date, time, text)
ENTRIES = [
    # ── November 2025 ──
    ("2025-11-10", "07:40", "Dr. Rao says I should write things down every day. So here I am. My name is Raghavan. I am 69. I live in the house on Temple Street. Writing that so I don't have to ask."),
    ("2025-11-10", "21:15", "Priya bought me this notebook-thing on the tablet. She showed me twice how to press the button. I feel silly talking to a screen, but she says it will help me keep hold of the days. Meera would have laughed at me. She always said I needed a diary because I never remembered her sister's birthday. Now I forget my own breakfast."),
    ("2025-11-12", "09:05", "Took the white tablet with breakfast. Donepezil. Writing it so I don't take it twice."),
    ("2025-11-14", "18:30", "Found my spectacles in the fridge next to the curd. No idea how."),
    ("2025-11-16", "19:45", "Sunday. Priya and Arjun came for lunch. Arjun is eight now, he corrected me when I said six. He showed me a card trick and I showed him how to multiply by eleven in his head. He was so pleased. For an hour I felt like a teacher again, not a patient. These are the good Sundays and I want to remember that they happen."),
    ("2025-11-20", "11:10", "Bruno and I walked to the park. Mr. D'Souza waved. Nice cold morning."),
    ("2025-11-23", "16:20", "Could not find the word for the thing you boil water in. Kettle. KETTLE."),
    ("2025-11-27", "20:05", "I went to the market for tomatoes and came back with three packets of biscuits and no tomatoes. The shopkeeper Selvam is patient with me. He just smiles and asks 'Sir, list?' I must carry the list. Priya has stuck a note on the door: KEYS, LIST, PHONE. I am a man who taught calculus for thirty-four years and now I need a note on the door."),

    # ── December 2025 ──
    ("2025-12-02", "08:15", "Woke up and reached for Meera's side. Then I remembered. Four years now."),
    ("2025-12-05", "21:40", "Bad day. I could not remember whether I had eaten lunch so I ate again, then felt sick. I sat in the garden and was angry at nothing in particular. Bruno sat on my feet the whole time. Dogs don't care if you remember lunch. I am writing this so tomorrow-me knows that bad days pass. This one is passing."),
    ("2025-12-09", "10:30", "Dr. Rao appointment. Memory test: I remembered 3 of 5 words. Apple, table, penny. Lost the others."),
    ("2025-12-14", "17:00", "Watered the jasmine. It is flowering even in December. Meera planted it."),
    ("2025-12-19", "19:10", "Vikram called from Toronto. Minus twelve there! I asked twice if he was eating well."),
    ("2025-12-25", "20:30", "Christmas at the D'Souzas' next door. Plum cake, carols, and their granddaughter played the piano. Mrs. D'Souza wrapped a slice of cake for me in foil and wrote 'Raghavan - cake' on it, because last year I apparently left it on their table. They didn't make me feel bad about it. Good neighbours are a kind of medicine."),
    ("2025-12-31", "23:50", "Last night of the year. Fireworks over the temple. I am still here. Still me, mostly."),

    # ── January 2026 ──
    ("2026-01-01", "09:00", "New year resolution: walk every morning, write every evening, be kind to myself when I forget."),
    ("2026-01-06", "14:20", "Feverish since last night. Throat like sandpaper. Staying in bed."),
    ("2026-01-07", "10:45", "Still sick. Priya came with rasam and paracetamol. She stayed the night on the sofa."),
    ("2026-01-08", "20:15", "Third day of this flu. Priya wrote the tablet times on a chart on the fridge with ticks, like I used to do for my students' homework. I noticed I could not remember yesterday at all, just the feeling of being tired. Dr. Rao said on the phone that illness makes the memory worse for a while and it comes back. I hope it comes back."),
    ("2026-01-10", "09:30", "Fever gone. Ate idli. Bruno very relieved, he has been sulking by the door."),
    ("2026-01-14", "19:00", "Pongal today! Priya made sweet pongal in the old brass pot. Arjun drew a kolam at the gate - crooked but beautiful. I remembered the whole Pongal song my mother used to sing, every verse. Strange how songs from 1962 stay perfectly and yesterday disappears. Priya recorded me singing it on her phone. I am glad someone has it now."),
    ("2026-01-21", "07:55", "Left the stove on with milk. It boiled over. Nothing burned. Must stand there till done."),
    ("2026-01-26", "11:30", "Republic Day parade on TV. Saluted from the sofa like a schoolboy."),
    ("2026-01-30", "18:40", "Could not remember Mr. D'Souza's first name. Felix. It's Felix. Known him 20 years."),

    # ── February 2026 ──
    ("2026-02-03", "10:00", "Priya installed a little gadget that switches off the gas if I forget. Good idea."),
    ("2026-02-08", "20:50", "Arjun's school day function. He was a tree in the play. A very serious tree. He had one line, 'The wind is coming!', and he shouted it so loudly the whole hall laughed. I was in the second row and I held Priya's hand. I want to keep this one. A serious little tree with a loud voice."),
    ("2026-02-13", "15:30", "Sorted old photos. Found Meera in her yellow saree at Mysore, 1981."),
    ("2026-02-14", "21:00", "Valentine's Day. We never celebrated it, Meera called it a greeting-card festival. But I kept her photo from Mysore on the table today and talked to her a while. Told her about Arjun the tree. Told her I am forgetting things. I think she would say, 'So? You never remembered where you kept the umbrella either.'"),
    ("2026-02-19", "12:15", "Paid electricity bill. Then almost paid it again. Wrote PAID on the bill in big letters."),
    ("2026-02-25", "17:45", "Felt dizzy in the garden. Sat down. Better after water and a banana."),

    # ── March 2026 ──
    ("2026-03-03", "19:30", "Holi! Arjun threw green powder all over my white kurta. I got him back with pink."),
    ("2026-03-08", "10:20", "Got lost on the way back from the temple. Only for twenty minutes, but twenty minutes on a road I have walked for thirty years. Everything looked like a photograph of itself. A young auto driver recognised me - I taught his father - and drove me home and refused money. I was frightened. I am writing it because Dr. Rao should know, and because I don't want to pretend it didn't happen."),
    ("2026-03-09", "09:10", "Priya bought me a watch that shows where I am on her phone. I don't mind."),
    ("2026-03-14", "22:10", "My 70th birthday. Seventy! Priya and Vikram arranged a surprise - Vikram was on a video call on the big TV, and his wife made the children sing in Tamil with Canadian accents. My old colleagues from the school came, Subbu and Lakshmi teacher. Subbu brought the staff photo from 1994. I remembered every face in it. Arjun gave me a card that said 'Thatha you are the best at maths and the worst at finding keys.' Both true. Best day in a long time."),
    ("2026-03-15", "08:30", "Woke up and saw the balloons and for a moment didn't know why. Then I read yesterday's entry. Happy."),
    ("2026-03-22", "16:00", "Planted tomato and chilli seedlings with Arjun. He named one tomato 'Gerald'."),
    ("2026-03-28", "20:00", "Blood pressure high today, 160/95. Less salt, Dr. Rao says. Life without pickle, imagine."),

    # ── April 2026 ──
    ("2026-04-02", "11:40", "Hot already. Bruno sleeps on the cool bathroom floor all afternoon. Smart dog."),
    ("2026-04-07", "21:20", "I asked Priya when Meera was coming home from her sister's. Priya went quiet and then gently told me. I don't remember asking, she told me tonight on the phone. It must have been terrible for her to hear. I feel ashamed and very sad, as if I lost Meera a second time today. I am writing it down: Meera passed away in October 2021. I am writing it so I don't make my daughter say it again."),
    ("2026-04-14", "09:45", "Tamil New Year. Mango pachadi - sweet, sour, bitter. Like life, Amma used to say."),
    ("2026-04-18", "18:10", "Did the crossword in the newspaper. Got 14 out of 20. Not bad for an old brain."),
    ("2026-04-25", "15:00", "Gerald the tomato has a flower. Arjun will be thrilled."),

    # ── May 2026 ──
    ("2026-05-02", "20:40", "Our wedding anniversary. Forty-six years if she were here. I went to the temple in the morning and lit a lamp. Then I made her favourite - curd rice with pomegranate - and ate it on the verandah where we used to sit. I couldn't remember the year we got married at first and it frightened me. Then it came: 1980, May 2nd, rain all morning, her father worried the whole time. It came back. Some things come back."),
    ("2026-05-06", "13:30", "Too hot to walk. Read Ramanujan's biography again. Third time? Maybe fourth."),
    ("2026-05-11", "07:20", "Fell asleep in the chair and woke at 4am thinking it was evening. Confusing."),
    ("2026-05-17", "19:15", "Arjun and I counted the ripe tomatoes - 11. He made me write the number down."),
    ("2026-05-24", "21:30", "Started a memory class at the community hall on Tuesdays. Eight of us, all grey heads. A lady named Kamala was a nurse for forty years, and now she forgets her daughter's phone number just like I forget mine. We laughed about it. It is easier to laugh with people who are in the same boat. The teacher gave us homework. Homework! At seventy!"),
    ("2026-05-29", "16:45", "Power cut for 5 hours. Sat outside with Felix. He talked about Goa; I listened."),

    # ── June 2026 ──
    ("2026-06-03", "08:00", "First rain of the monsoon! The whole street smells of wet earth. I stood in it."),
    ("2026-06-04", "10:30", "Sneezing since yesterday. That is what standing in the rain at seventy gets you."),
    ("2026-06-09", "17:20", "Memory class: we each brought a photo and told its story. I took the 1994 staff photo."),
    ("2026-06-15", "20:20", "Father's Day. Vikram called early in the morning, his evening. Priya brought a framed drawing from Arjun - me with Bruno and an enormous tomato. In the drawing I am smiling with all my teeth, which I don't have anymore. I've stuck it on the wall by the door, next to the KEYS LIST PHONE note. It feels right that they are together."),
    ("2026-06-21", "07:00", "Yoga Day. Did five minutes of stretching. Knees complained loudly."),
    ("2026-06-27", "12:40", "Could not find the remote. It was in the bread box. Bruno is not a suspect."),

    # ── July 2026 ──
    ("2026-07-04", "22:00", "Vikram is HOME! Flew in with Anjali and the two kids for three weeks. The house is so loud. I kept calling his daughter Priya, which made everyone laugh, and his son corrected me patiently each time. 'Thatha, I'm Rohan. R-O-H-A-N.' I wrote all the names on the whiteboard in the kitchen: Vikram, Anjali, Rohan (11), Meenu (7). Meenu - named after Meera."),
    ("2026-07-09", "18:30", "Took the whole family to Mahabalipuram. Rohan climbed everything. I sat with Meenu by the shore."),
    ("2026-07-14", "21:10", "Vikram sat with me late tonight and asked how I really am. Not the polite answer. I told him the truth: some mornings I wake up and the room is a stranger, and I have to read this journal to find myself. He cried a little. My son, forty-three years old, crying at my kitchen table. I told him what my father told me: you don't have to fix it, you only have to visit. He promised to call every Sunday."),
    ("2026-07-25", "06:30", "They left for the airport at 4am. House is too quiet. Bruno keeps checking the guest room."),
    ("2026-07-28", "15:10", "Found a drawing from Meenu under my pillow. A heart and 'THATHA DON'T FORGET ME'."),

    # ── August 2026 ──
    ("2026-08-04", "09:00", "Slipped in the bathroom this morning. Hip hurts badly. Called Priya - she is coming."),
    ("2026-08-04", "22:45", "Hospital. X-ray says no fracture, just a deep bruise, thank God. The nurses keep asking me the date and the name of the Prime Minister. I got the Prime Minister right and the date wrong. Priya is sleeping in the chair beside me with her mouth open, like she did as a little girl on train journeys. I'm frightened of being a burden. I'm writing so I remember she stayed."),
    ("2026-08-06", "14:00", "Discharged. Walking with a stick. Priya put a rubber mat and a grab bar in the bathroom."),
    ("2026-08-10", "19:30", "Hip still sore. Dark mood. Sat by the window most of the day. Didn't write much."),
    ("2026-08-15", "10:15", "Independence Day. Watched the flag hoisting from the gate with Felix. Stood up for the anthem, stick and all."),
    ("2026-08-22", "20:00", "Physio exercises done. The physio lady says I am 'very disciplined'. Old teacher habit."),
    ("2026-08-28", "21:00", "Raksha Bandhan was yesterday, Priya says, and I missed it entirely - didn't call my sister Saroja in Madurai. I called her today to apologise. She laughed and said she had forgotten too. Two old people forgetting each other, she said, is still remembering in its own way. We talked for an hour about our father's bicycle. Good call."),

    # ── September 2026 ──
    ("2026-09-04", "08:45", "Walked to the park without the stick! Slowly. Bruno waited for me at every corner."),
    ("2026-09-05", "20:10", "Teachers' Day. Three former students messaged me. One is a professor now in Pune. He wrote: 'Sir, you made me love numbers.' I read it many times today. I may forget that I read it, but it will be here, in the Archives, and I can read it again tomorrow and be just as happy. That is the strange gift of a bad memory - good news stays new."),
    ("2026-09-11", "11:30", "Dr. Rao: memory scores stable since March. Stable is good, she says. I'll take stable."),
    ("2026-09-14", "19:00", "Ganesh Chaturthi. Arjun made a clay Ganesha. Its trunk fell off. We used a toothpick."),
    ("2026-09-19", "16:30", "Couldn't remember if I fed Bruno. Bruno insisted I hadn't. Bruno lies."),
    ("2026-09-26", "21:45", "Woke from a nap and was sure I was late for school - I had to give a test to class 10B. I put on my shirt and found my old briefcase before I understood. I am retired since 2016. It was frightening, then a bit funny. I sat down and wrote this so I can see it in daylight. Felix came by and I told him I almost went to teach. He said, 'Teach me then,' and I taught him the trick with the number 1089."),

    # ── October 2026 ──
    ("2026-10-02", "10:00", "Gandhi Jayanti. Cleaned the garden shed as a small seva. Found Meera's gardening gloves."),
    ("2026-10-08", "13:15", "Cough and chest feels heavy. Doctor gave antibiotics. Resting."),
    ("2026-10-10", "18:20", "Still coughing at night. Priya brought steam inhaler and a hot-water bottle."),
    ("2026-10-13", "09:30", "Cough nearly gone. Bruno and I sat in the sun for an hour. Medicine of the best kind."),
    ("2026-10-19", "20:30", "Navaratri - Priya set up the golu dolls. The old dolls from Meera's mother came out of the trunk, wrapped in her newspapers from 1998. I unwrapped each one and remembered where Meera used to place it: the wedding set on the third step, the Chettiar shop at the bottom. Priya let me arrange it exactly that way. My hands remembered what my head did not."),
    ("2026-10-21", "11:00", "Vijayadashami. Arjun wrote his first Sanskrit letter on the rice plate. I guided his hand."),
    ("2026-10-24", "17:50", "Fourth death anniversary of Meera this week. Lit a lamp. Did not cry today. Remembered her laugh."),
    ("2026-10-30", "12:30", "Forgot my memory class on Tuesday. Kamala called to check on me. Nice to be missed."),

    # ── November 2026 ──
    ("2026-11-03", "19:40", "Arjun's ninth birthday party. Cake shaped like a cricket bat. I gave him my old geometry box."),
    ("2026-11-06", "16:00", "Diwali shopping with Priya. I chose a sparkler box for Arjun. Remembered the list!"),
    ("2026-11-08", "22:30", "Diwali. The whole street was lit. Priya, Arjun, Felix and his wife sat on our verandah, and Vikram's family joined on video from Toronto at 6am their time, still in pyjamas. Arjun and I lit the lamps along the wall - 70 of them, one for each year, his idea. I forgot to eat my medicine at dinner, Priya reminded me. I did not forget a single face tonight. One year of this journal. Thank you, notebook-thing."),
    ("2026-11-09", "08:20", "Read last year's first entry. I am Raghavan. I am 70. Still on Temple Street. Still here."),
]


def build_rows(profile_id):
    return [
        {
            "content": text,
            "profile_id": profile_id,
            "created_at": f"{date}T{time}:00{TZ}",
        }
        for date, time, text in ENTRIES
    ]


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        rows = build_rows("dry_run_user")
        for r in rows:
            kind = "SNIPPET   " if len(r["content"]) <= 150 else "REFLECTION"
            print(f"{r['created_at']}  {kind}  {r['content'][:80]}")
        snippets = sum(1 for r in rows if len(r["content"]) <= 150)
        print(f"\n{len(rows)} entries ({snippets} snippets, {len(rows) - snippets} reflections)")
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
    rows = build_rows(user_id)
    sb.table("journal_slates").insert(rows).execute()
    print(f"Inserted {len(rows)} journal entries into The Archives (Nov 2025 - Nov 2026).")


if __name__ == "__main__":
    main()
